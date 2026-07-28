# `common.py` 函数功能说明书

对应文件：[`scripts/common.py`](../scripts/common.py)

被 `00`～`04` 脚本导入：

```python
from common import demo_root, reset_dir, run_git, ...
```

本身**不含演示剧情**，只提供可复用辅助函数。依赖：Python ≥ 3.10 标准库 + 系统 `git`。

---

## 函数一览

| 函数 | 作用 |
| --- | --- |
| [`demo_root`](#demo_root) | 定位演示仓库根目录 |
| [`reset_dir`](#reset_dir) | 清空并重建某个工作目录 |
| [`init_bare`](#init_bare) | 创建默认分支为 main 的裸远程 |
| [`run_git` / `git_ok` / `git_out`](#run_git) | 调用系统 Git |
| [`init_clone`](#init_clone) | 克隆远程并设置该克隆的作者信息 |
| [`write_utf8`](#write_utf8) | 以无 BOM 的 UTF-8 + LF 写文件 |
| [`show_graph`](#show_graph) | 打印某仓库的提交图谱 |
| [`rebase_in_progress` / `merge_in_progress`](#rebase_in_progress--merge_in_progress) | 检测进行中的 rebase / merge |
| [`write_json` / `read_json`](#write_json--read_json) | 读写场景元数据 |
| [`require_git` / `ensure_python`](#require_git--ensure_python) | 启动前检查环境 |

---

## `demo_root`

返回 `scripts/` 的上一级（演示项目根目录）绝对路径。

```python
root = demo_root()
ws = root / "workspaces"
```

---

## `reset_dir`

保证目标路径是空目录：存在则尽量删除（含 `*.lock`；删不掉则改名备份），再 `mkdir`。

```python
reset_dir(root / "workspaces")
```

---

## `init_bare`

```python
init_bare(remote)                 # 默认 initial_branch="main"
# 等价：
# git init --bare -b main <path>
# git --git-dir=<path> symbolic-ref HEAD refs/heads/main
```

避免裸仓 HEAD 停在 `master`，导致 clone 后本地默认分支与 `push -u origin main` 不一致。

---

## `run_git`

用 `subprocess` 调用系统 `git`。默认捕获 stdout/stderr；设置 `GIT_EDITOR=true` 避免 rebase 弹编辑器。

```python
run_git("status", cwd=bob, check=True)
run_git("log", "--oneline", git_dir=remote)  # 针对裸仓
```

- `git_ok(...)` → 是否成功（bool）
- `git_out(...)` → 去掉首尾空白的 stdout

---

## `init_clone`

```python
init_clone(remote, alice, "Alice", "alice@example.com")
```

等价于 `git clone` + 该仓库内的 `user.name` / `user.email`（不改全局配置）。

---

## `write_utf8`

UTF-8 无 BOM、换行统一为 LF，避免跨平台提交哈希不一致。

```python
write_utf8(alice / "README.md", "# Team Chat\n\nshared baseline\n")
```

---

## `show_graph`

```python
show_graph(bob, "Bob AFTER conventional pull")
# → git log --oneline --graph --all --decorate -20
```

---

## `rebase_in_progress` / `merge_in_progress`

检查 `.git/rebase-merge`（或 `rebase-apply`）、`.git/MERGE_HEAD`。

---

## `write_json` / `read_json`

场景 A 把 `oldTip` 等写入 `workspaces/scenario-A-meta.json`，供脚本 03 使用。

---

## `require_git` / `ensure_python`

- `ensure_python()`：要求 Python ≥ 3.10
- `require_git()`：要求 `git` 在 PATH 中

---

## 谁在用

| 脚本 | 主要用到的函数 |
| --- | --- |
| `00-reset-workspace.py` | `reset_dir`、`init_clone`、`run_git` |
| `01-scenario-A-...py` | 几乎全部 |
| `02-wrong-merge-resolve.py` | `write_utf8`、`show_graph`、`run_git` |
| `03-proper-recovery-onto.py` | `read_json`、`write_utf8`、`rebase_*` |
| `04-scenario-B-...py` | 几乎全部（目录为 `workspaces-lost`） |

回到索引：[docs/README.md](./README.md)
