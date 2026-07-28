#!/usr/bin/env python3
"""Proper recovery after WRONG merge: reset, find oldTip, rebase --onto.

Usage (after 02-wrong-merge-resolve.py):
  python scripts/03-proper-recovery-onto.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    demo_root,
    ensure_python,
    git_out,
    read_json,
    rebase_in_progress,
    require_git,
    run_git,
    show_graph,
    write_utf8,
)


def resolve_old_tip(bob: Path, ws: Path) -> str:
    """Prefer HEAD^ (emoji parent) as the real-world way; meta as fallback."""
    tip = git_out("rev-parse", "--short", "HEAD^", cwd=bob)
    print(f"oldTip from HEAD^ (emoji parent): {tip}")

    meta_path = ws / "scenario-A-meta.json"
    if meta_path.is_file():
        meta_tip = read_json(meta_path).get("oldTip", "").strip()
        if meta_tip:
            short = git_out("rev-parse", "--short", meta_tip, cwd=bob)
            print(f"(scenario-A-meta.json recorded: {short})")
    return tip


def main() -> None:
    ensure_python()
    require_git()
    root = demo_root()
    ws = root / "workspaces"
    bob = ws / "bob"
    if not bob.is_dir():
        raise SystemExit(
            "Run 01-scenario-A-duplicate-history.py "
            "and 02-wrong-merge-resolve.py first."
        )

    latest_msg = git_out("log", "-1", "--pretty=%s", cwd=bob)
    if "WRONG" not in latest_msg:
        raise SystemExit(
            "Expected a WRONG merge at HEAD (run 02-wrong-merge-resolve.py first).\n"
            f"Current HEAD: {latest_msg}"
        )

    print("WRONG merge detected — reset --hard HEAD~1 to undo it...")
    run_git("reset", "--hard", "HEAD~1", cwd=bob, check=True)

    head_msg = git_out("log", "-1", "--pretty=%s", cwd=bob)
    print(f"HEAD now: {head_msg}")

    old_tip = resolve_old_tip(bob, ws)
    print("Proper recovery (Pro Git: Recovering from Upstream Rebase):")
    print(f"  git rebase --onto origin/feature {old_tip} feature")
    print()

    run_git("fetch", "origin", cwd=bob, check=True)
    rebase = run_git(
        "rebase", "--onto", "origin/feature", old_tip, "feature",
        cwd=bob,
        check=False,
    )
    if rebase.returncode != 0 or rebase_in_progress(bob):
        print("Conflict while replaying Bob-only commit - resolve once, then continue:")
        write_utf8(
            bob / "README.md",
            "# Team Chat\n\n"
            "- security patch on main\n"
            "- login\n"
            "- messages\n"
            "- emoji reactions (Bob WIP)\n",
        )
        write_utf8(
            bob / "app.py",
            "VERSION = '0.2'\n\n"
            "def greet(name):\n"
            "    return f'Hello, {name}!'\n\n"
            "def login(user, password):\n"
            "    return user == 'admin' and password == 'secret'\n\n"
            "def send_message(user, text):\n"
            "    return f'{user}: {text}'\n\n"
            "def add_reaction(msg, emoji):\n"
            "    return f'{msg} {emoji}'\n",
        )
        run_git("add", "README.md", "app.py", cwd=bob, check=True)
        run_git("rebase", "--continue", cwd=bob, check=False)

    show_graph(bob, "After proper rebase --onto (NO duplicate login/send_message)")
    print()
    print("Compare: only ONE 'add login' and ONE 'send_message' on the path to HEAD.")
    print(run_git("log", "--oneline", "--grep=add login", cwd=bob).stdout or "", end="")
    print(run_git("log", "--oneline", "--grep=send_message", cwd=bob).stdout or "", end="")
    print()
    print("Bob can now push normally (no force needed if he never pushed emoji commit).")


if __name__ == "__main__":
    main()
