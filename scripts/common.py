"""Shared helpers for rebase-on-public-branch demos (Windows / Linux)."""

from __future__ import annotations

import json
import os
import random
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable


SCRIPTS_DIR = Path(__file__).resolve().parent
DEMO_ROOT = SCRIPTS_DIR.parent


def demo_root() -> Path:
    return DEMO_ROOT


def _clear_readonly(path: Path) -> None:
    """Git objects on Windows are often read-only; clear before delete."""
    if not path.exists():
        return
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files + dirs:
            p = Path(root) / name
            try:
                os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
            except OSError:
                pass
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    except OSError:
        pass


def _rmtree_force(path: Path) -> None:
    def _onexc(func: Callable[..., Any], p: str, _exc: BaseException) -> None:
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass

    shutil.rmtree(path, onexc=_onexc)


def _rmdir_windows(path: Path) -> bool:
    """Last-resort Windows delete (handles some stubborn locks better)."""
    if os.name != "nt":
        return False
    # rmdir /s /q
    subprocess.run(
        ["cmd", "/c", "rmdir", "/s", "/q", str(path)],
        check=False,
        capture_output=True,
    )
    if not path.exists():
        return True
    # robocopy mirror-empty trick
    empty = path.with_name(f"{path.name}-empty-{random.randint(0, 10**9)}")
    try:
        empty.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["robocopy", str(empty), str(path), "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NC", "/NS"],
            check=False,
            capture_output=True,
        )
        shutil.rmtree(empty, ignore_errors=True)
        shutil.rmtree(path, ignore_errors=True)
    except OSError:
        shutil.rmtree(empty, ignore_errors=True)
    return not path.exists()


def reset_dir(path: Path) -> None:
    """Clear and recreate a directory (best-effort if IDE locks files)."""
    if path.exists():
        for lock in path.rglob("*.lock"):
            try:
                lock.unlink(missing_ok=True)
            except OSError:
                pass

        last_exc: OSError | None = None
        for attempt in range(5):
            try:
                _clear_readonly(path)
                _rmtree_force(path)
            except OSError as exc:
                last_exc = exc
            if not path.exists():
                break
            if _rmdir_windows(path):
                break
            # Rename aside so a fresh dir can still be created
            bak = path.with_name(f"{path.name}-old-{random.randint(0, 10**9)}")
            try:
                _clear_readonly(path)
                path.rename(bak)
                break
            except OSError as exc:
                last_exc = exc
                time.sleep(0.25 * (attempt + 1))

        if path.exists():
            raise RuntimeError(
                f"Cannot clear {path} (file lock).\n"
                "Close editor tabs under workspaces/, stop other debug sessions, "
                "and ensure no terminal cwd is inside that folder, then retry."
            ) from last_exc
    path.mkdir(parents=True, exist_ok=True)


def init_bare(path: Path, initial_branch: str = "main") -> None:
    """Create a bare remote whose HEAD defaults to main (not master)."""
    run_git("init", "--bare", "-b", initial_branch, str(path), check=True)
    # Belt-and-suspenders for older Git / odd templates
    run_git("symbolic-ref", "HEAD", f"refs/heads/{initial_branch}", git_dir=path, check=True)


def run_git(
    *args: str,
    cwd: Path | None = None,
    check: bool = False,
    capture: bool = True,
    env: dict[str, str] | None = None,
    git_dir: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = ["git"]
    if git_dir is not None:
        cmd.extend(["--git-dir", str(git_dir)])
    cmd.extend(args)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    # Avoid editor prompts during rebase --continue etc.
    merged_env.setdefault("GIT_EDITOR", "true")
    merged_env.setdefault("GIT_SEQUENCE_EDITOR", "true")
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=check,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=merged_env,
    )


def git_ok(*args: str, cwd: Path | None = None, **kwargs: Any) -> bool:
    return run_git(*args, cwd=cwd, check=False, **kwargs).returncode == 0


def git_out(*args: str, cwd: Path | None = None, **kwargs: Any) -> str:
    proc = run_git(*args, cwd=cwd, check=False, **kwargs)
    return (proc.stdout or "").strip()


def init_clone(remote: Path, path: Path, name: str, email: str) -> None:
    """ 初始化仓库，并设置用户名和邮箱
    用法: init_clone(<remote>, <path>, <name>, <email>)
    示例: init_clone("/workspaces/origin.git", "/workspaces/alice", "Alice", "alice@example.com")
    示例: init_clone("/workspaces/origin.git", "/workspaces/bob", "Bob", "bob@example.com")
    
    这里没有使用git -C config（切换路径）
    是因为用的subprocess.run，而不是git命令行，调用时指定运行目录path，不需要-C参数切换路径

    git clone <remote> <path>
    git config user.name <name>
    git config user.email <email>
    """
    run_git("clone", str(remote), str(path), check=False)
    if not (path / ".git").exists():
        raise RuntimeError(f"git clone failed: {path}")
    run_git("config", "user.name", name, cwd=path, check=True)
    run_git("config", "user.email", email, cwd=path, check=True)


def write_utf8(path: Path, content: str) -> None:
    """UTF-8 without BOM, LF line endings (stable hashes across OS)."""
    text = content.replace("\r\n", "\n")
    path.write_text(text, encoding="utf-8", newline="\n")


def show_graph(repo: Path, title: str) -> None:
    print()
    print(f"===== {title} =====")
    proc = run_git(
        "log", "--oneline", "--graph", "--all", "--decorate", "-20",
        cwd=repo,
        capture=True,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")


def rebase_in_progress(repo: Path) -> bool:
    git_dir = repo / ".git"
    return (git_dir / "rebase-merge").is_dir() or (git_dir / "rebase-apply").is_dir()


def merge_in_progress(repo: Path) -> bool:
    return (repo / ".git" / "MERGE_HEAD").is_file()


def status_porcelain(repo: Path) -> str:
    return git_out("status", "--porcelain", cwd=repo)


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_utf8(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_git() -> None:
    try:
        proc = run_git("--version", check=False)
    except FileNotFoundError as exc:
        raise SystemExit("git not found on PATH. Install Git and retry.") from exc
    if proc.returncode != 0:
        raise SystemExit("git not found on PATH. Install Git and retry.")


def ensure_python() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit(f"Python >= 3.10 required, got {sys.version}")
