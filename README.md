# 公共分支上 Rebase 的危害（实操演示）

用 **Alice / Bob** 双人协作复现：对**已推送、他人正在用**的分支做 `rebase` + 强推后，常规 `pull` / `merge` **救不干净**。

> 原则（Pro Git）：**不要在公共分支上 rebase。**  
> 本实验故意违反，亲手踩坑。

实验步骤（可复制粘贴手搓）见 [docs/](./docs/README.md)；也可直接跑 `scripts/` 一键脚本。

---

## 环境

- Python ≥ 3.10（建议 3.12，见 `.python-version` / `pyproject.toml`）
- Git ≥ 2.23（需要 `git switch`）
- 无第三方 pip 依赖

```bash
python --version
git --version
```

建议先配图谱别名（详见 [01 实验准备](./docs/01-场景A-实验准备.md)）：

```bash
git config --global alias.lg "log --oneline --graph --all --decorate"
```

---

## 怎么练

| 文档 | 脚本 | 内容 |
| --- | --- | --- |
| [01-场景A-实验准备](./docs/01-场景A-实验准备.md) | `00-reset-workspace.py` | 清空 workspaces + 裸仓 + Alice/Bob |
| [02-场景A-实验步骤](./docs/02-场景A-实验步骤.md) | `01-scenario-A-...py` | 公共 rebase → Bob pull 冲突 |
| [03-场景A-错误解冲突](./docs/03-场景A-错误解冲突.md) | `02-wrong-merge-resolve.py` | 常规 3-way → 双胞胎提交 |
| [04-场景A-正确恢复](./docs/04-场景A-正确恢复.md) | `03-proper-recovery-onto.py` | reset + 找 oldTip + `rebase --onto` |
| [05-场景B-实验步骤](./docs/05-场景B-实验步骤.md) | `04-scenario-B-...py` | `--force` 抹掉他人已推送提交 |

建议顺序：

1. **01 → 02**：在 `workspaces/bob` 看冲突与分叉  
2. **03**：体会「代码对了、历史废了」  
3. **04**：撤掉 WRONG merge，自己找截取点，`--onto`  
4. **05**（独立目录 `workspaces-lost/`）：对比 lease 与裸 force  

```bash
python scripts/00-reset-workspace.py
python scripts/01-scenario-A-duplicate-history.py
```

---

## 场景 A：内容「一样」，哈希不一样

### 情况说明（提交链）

记两条链：

| 缩写 | 含义 |
| --- | --- |
| `ilse` | Bob 本地：`init → login → send → emoji`（emoji 可尚未推送） |
| `imls` | Alice 强推后远程：`init → mix → login' → send'` |

发生过程：

1. 一开始公共 `feature` 是 `init → login → send`（Alice / Bob 都基于它）。
2. Alice 在 `main` 上做了 `mix`（security patch），为了本地历史干净，把 `login` / `send` **rebase** 到新 `main` 上 → 变成 `init → mix → login' → send'`。
3. **关键错误**：Alice 把 rebase 后的提交**强推**到公共 `feature`。  
   Bob 这边同名的 `login` / `send` **代码几乎一样，但父节点变了 → SHA 全变**（双胞胎提交）。
4. Bob 本地还有自己的 `emoji`，再 `pull`：msg 不清、内容没细看，Git 只能当两段历史做 **3-way merge**。

一键到冲突态：

```bash
python scripts/01-scenario-A-duplicate-history.py
cd workspaces/bob
git lg
git status    # UU / both modified
```

### 错误解法：3-way「全都要」

Bob 按老习惯：README / `app.py` 全量覆盖 → `add` → `commit`。

- 工作区可以「看起来正确」
- 历史上 **login / send_message 各两条**（同 message、不同 SHA），WRONG merge 把旧链和新链都钉死了

```bash
python scripts/02-wrong-merge-resolve.py
cd workspaces/bob
git lg
git log --oneline --all --grep="add login"
git log --oneline --all --grep="send_message"
```

图见 [03](./docs/03-场景A-错误解冲突.md)。

### 正确恢复：reset + `rebase --onto`（取尾不取头）

目标：**以 Alice 强推后的远程为准**，只把自己真正多出来的 `emoji` 挪过去；消化掉旧 `login` / `send`。

1. `git reset --hard HEAD~1` —— 撤掉 WRONG 3-way merge（emoji 仍在旧 tip 上）
2. `fetch` 后在图谱上找到**变基前公共 tip**（旧 `send` 那个点，即 `--onto` 的 `<from>`）
3. `git rebase --onto origin/feature <from> HEAD`  
   - **取尾不取头**：`<from>` **不包含**，只重放其后真正属于自己的提交  
   - rebase **按补丁内容**重放，不会因为「同内容不同 SHA」再当成两段历史硬 merge
4. 推上去后，Alice 侧应是 **ff-merge**，而不是双胞胎 3-way

```text
# 示意：取 B..E（含 E 不含 B）接到 H
A - B - C - D - E     (旧 feature)
    |
    F - G - H         (新底座 / origin/feature)

git rebase --onto H B E
→  H - C' - D' - E'
```

```bash
# 从脏历史接着救（或重跑 00→01→02 后再做）
python scripts/03-proper-recovery-onto.py
# 手搓要点见 docs/04；核心形如：
# git reset --hard HEAD~1
# git rebase --onto origin/feature <oldTip> HEAD
```

验证：`login` / `send_message` 各只剩 **一条**，emoji 在新底座之上。图见 [04](./docs/04-场景A-正确恢复.md)。

---

## 场景 B：`--force` 抹掉别人已上远程的提交

与场景 A 独立，目录：`workspaces-lost/`。

1. Bob 已把 `CRITICAL` **push** 到公共 `feature`
2. Alice **没 fetch**，本地仍停在更早 tip
3. Alice rebase 到新 `main` 后：
   - `push --force-with-lease` → **应拒绝**（远程已前进）
   - `push --force` → **覆盖成功**，远程再看不到 Bob 的 CRITICAL
4. Alice 再 `pull` 也找不回；只能靠仍持有该对象的人（Bob 本地）`cherry-pick` / 再推

```bash
python scripts/04-scenario-B-lost-commits.py
```

手搓步骤见 [05](./docs/05-场景B-实验步骤.md)。

---

## 两场景对照

| | 场景 A | 场景 B |
| --- | --- | --- |
| 触发 | 公共分支 rebase + 强推 | 过期本地 + 裸 `--force` |
| 表象 | 双胞胎提交、3-way 冲突 | 他人提交从远程「消失」 |
| 常规 pull/merge | 历史更脏 | 找不回丢失提交 |
| 出路 | `reset` + `rebase --onto`（取尾不取头） | 从仍持有对象的克隆抢救 |
| 根因 | 父节点改写 → SHA 变 | 分支引用被强推挪走 |

---

## 目录结构

```
rebase-conflict-demo/
├── README.md
├── docs/                 ← 手搓步骤 + 图
├── scripts/              ← 00～04 一键脚本 + common.py
├── workspaces/           ← 场景 A 生成（gitignore）
└── workspaces-lost/      ← 场景 B 生成（gitignore）
```

---

## 带走的结论

1. **已推送且有人基于它开发的分支，不要 rebase**；公共分支用 merge 更安全。
2. Rebase 是**复制出新提交**（新父节点 → 新哈希），不是原地改。
3. 别人再 3-way 合回来，Git 当两段无关历史 → 双胞胎 + 冲突。
4. 救法不是再 pull 一次，而是 **撤掉错误 merge**，用 `rebase --onto` **只挪自己的尾部提交**。
5. 强推至少用 `--force-with-lease`，且先 `fetch`；裸 `--force` 可以抹掉别人已上远程的提交。
