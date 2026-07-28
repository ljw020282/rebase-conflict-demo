# 公共分支上 Rebase 的危害（实操演示）

本仓库用 **Alice / Bob 双人协作** 复现：对**已经推送、他人正在使用**的分支执行 `rebase` + 强推后，常规 `pull` / `merge` **无法干净收场**的严重后果。

> 原则（Pro Git）：**不要在公共分支上 rebase。**  
> 本实验故意违反该原则，复现冲突。

---

## 环境要求

- **Python ≥ 3.10**（见 `.python-version` / `pyproject.toml`）
- **Git ≥ 2.23**（需要 `git switch`）
- 无第三方 pip 依赖（`requirements.txt` 为空说明）

```bash
python -m pip install -r requirements.txt   # 可选；当前无包可装
python --version   # 确认 >= 3.10
git --version
```

## 目录结构

```
rebase-conflict-demo/
├── README.md                 ← 本指南（总览）
├── pyproject.toml            ← requires-python >= 3.10
├── requirements.txt          ← 无第三方依赖（仅文档）
├── .python-version           ← 建议 3.12
├── docs/                     ← 实验步骤（可复制粘贴手搓）
│   ├── README.md
│   ├── 01-场景A-实验准备.md
│   ├── 02-场景A-实验步骤.md
│   ├── 03-场景A-错误解冲突.md
│   ├── 04-场景A-正确恢复.md
│   ├── 05-场景B-实验步骤.md
│   └── common.md             ← common.py 函数说明书
├── scripts/
│   ├── common.py             ← 公共辅助函数
│   ├── 00-reset-workspace.py ← 只搭空环境（手动演练用）
│   ├── 01-scenario-A-...     ← 场景A：重复提交 + 3-way 冲突
│   ├── 02-wrong-merge-...    ← 用「常规解冲突」把历史弄脏
│   ├── 03-proper-recovery... ← 正确恢复：rebase --onto
│   └── 04-scenario-B-...     ← 场景B：--force 抹掉他人已推送提交
├── workspaces/               ← 场景A 生成（alice / bob / origin.git）
└── workspaces-lost/          ← 场景B 生成
```

手动验证时打开实验步骤，按文档复制 git 命令与文件内容：

- [docs/README.md](./docs/README.md) — 索引与建议顺序
- [docs/01-场景A-实验准备.md](./docs/01-场景A-实验准备.md)
- [docs/02-场景A-实验步骤.md](./docs/02-场景A-实验步骤.md)
- [docs/03-场景A-错误解冲突.md](./docs/03-场景A-错误解冲突.md)
- [docs/04-场景A-正确恢复.md](./docs/04-场景A-正确恢复.md)
- [docs/05-场景B-实验步骤.md](./docs/05-场景B-实验步骤.md)
- [docs/common.md](./docs/common.md) — `common.py` 函数说明书

也可以直接跑脚本（Windows / Linux / macOS 相同）：

```bash
python scripts/01-scenario-A-duplicate-history.py
```

---



## 场景 A：内容「一样」，哈希不一样 → 常规 merge 灾难



### 发生了什么

1. `feature` 是**公共分支**，Alice / Bob 都往上面推过。
2. `main` 前进后，Alice 对 `feature` 做 `git rebase main`，再 `push --force`。
3. Rebase **改写了每个提交的父节点** → **SHA 全变**；提交说明几乎一样，补丁内容也类似。
4. Bob 本地还有基于**旧哈希**的提交。他执行常规：
  ```text
   git pull          # 默认 3-way merge
  ```
5. Git 不认为两边是「同一批提交」，而是两段**分叉历史** → 冲突 + 即将产生**重复提交**。



### 你要亲眼确认的现象

```bash
python scripts/01-scenario-A-duplicate-history.py
cd workspaces/bob
git status
git log --oneline --graph --all
cat README.md   # 冲突标记（Windows 也可用 type README.md）
```

重点看图：

- 一侧：`login` / `send_message`（**旧 SHA**）
- 另一侧：同名提交（**新 SHA**，父节点已是新 `main`）
- 分支提示：`have diverged`



### 「常规方法」为什么救不了


| 常规操作 | 结果 |
| --- | --- |
| 手解冲突 + `git commit`（完成 merge） | 工作区可能正常，但历史里 **login / send_message 各出现两次** |
| 再 `git pull` / `git merge` | 无法去掉重复节点 |
| 再 `git rebase` | 往往再次冲突，重复补丁继续纠缠 |
| `git revert` merge | 可达历史仍保留两侧旧提交 |


跑一遍「错误解法」：

```bash
# 须在 01 产生的冲突状态下立即运行
python scripts/02-wrong-merge-resolve.py
```

然后执行：

```powershell
git log --oneline --all --grep="add login"
git log --oneline --all --grep="send_message"
```

你会看到**同 message、不同 SHA** —— 这就是「父节点变了，哈希变了」的铁证。

### 正确恢复（仍需特殊命令，不是日常 pull）

若**还没**跑 02，在冲突或仅分叉时：

```bash
python scripts/03-proper-recovery-onto.py
```

核心命令（Pro Git: *Recovering from Upstream Rebase*）：

```bash
git merge --abort          # 若已在错误 merge 中
git rebase --onto origin/feature <旧公共 tip> feature
```

含义：只把「旧 tip **之后**、真正属于自己的提交」挪到**新的**远程历史上；不要把已被 rebase 过的旧提交再 merge 进来。

> 若已经跑过 02，历史已脏：请重新跑 01，**跳过 02**，直接跑 03。

---



## 场景 B：强推直接弄丢别人已上远程的提交



### 发生了什么

1. Bob 已把 `CRITICAL` 提交 **push 到公共** `feature`。
2. Alice **没有 fetch**，本地仍停在更早的 tip。
3. Alice `rebase` 到新 `main` 后执行 `git push --force`。
4. 远程 `feature` 指针跳走 → Bob 的提交**不再被任何分支指向**。



### 你要亲眼确认的现象

```bash
python scripts/04-scenario-B-lost-commits.py
```

脚本会演示：

1. `--force-with-lease`：**拒绝**覆盖（远程已前进，Alice 本地远程跟踪仍旧）。
2. Alice 改用 `--force`：**覆盖成功**，远程图上再也看不到 Bob 的 CRITICAL。
3. 对象可能暂时还在对象库里，但**无分支引用**；别人若从未拉过、或 reflog 过期 → **实质丢失**。

Alice 侧再怎么 `git pull` 也找不回 B1——它本来就不在她改写后的历史上。

恢复只能依赖：**仍持有该 commit 的人**（Bob 本地 / 备份 / 服务器 reflog）去 `cherry-pick` 或重新推送。

---



## 两个场景对照：为何算「严重且非常规」


| | 场景 A | 场景 B |
| --- | --- | --- |
| 触发 | 公共分支 rebase + 强推 | 过期本地 rebase + `--force` |
| 表象 | 冲突、重复提交、分叉 | 他人提交从远程「消失」 |
| 常规 pull/merge | 制造更脏的历史 | 无法找回丢失提交 |
| 真正出路 | `rebase --onto` 等恢复流程 | 从仍持有对象的克隆抢救 |
| 根因 | **父节点被改写 → SHA 变化** | **引用被强推挪走** |


---



## 实操建议顺序

1. [01](./docs/01-场景A-实验准备.md) → [02](./docs/02-场景A-实验步骤.md) → 在 `workspaces/bob` 看冲突与图谱。
2. [03](./docs/03-场景A-错误解冲突.md) → 体会「代码对了、历史废了」。
3. 重做 01+02，跳过 03，做 [04](./docs/04-场景A-正确恢复.md) → 对比干净历史。
4. [05](./docs/05-场景B-实验步骤.md) → 对比 `--force-with-lease` 与 `--force`。

---



## 带走的结论

1. **已推送且有人基于它开发的分支，不要 rebase。** 用 merge 更新公共分支更安全。
2. Rebase 的本质是**复制出新提交**（新父节点 → 新哈希），不是「原地改」。
3. 别人再用 3-way merge 合回来，Git 会当成两段无关历史 → 重复 + 冲突。
4. `--force` 能抹掉远程上别人的提交；至少改用 `--force-with-lease`，且**先 fetch**。
5. 一旦发生上游 rebase，同伴需要的是 `rebase --onto` **恢复手册**，不是再一次「普通 pull」。

