#!/usr/bin/env python3
"""Wrong fix: resolve merge conflicts normally -> duplicate commits in history.

Prerequisite: run 01, with Bob still in a conflicted merge.

Usage:
  python scripts/02-wrong-merge-resolve.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    demo_root,
    ensure_python,
    require_git,
    run_git,
    show_graph,
    status_porcelain,
    write_utf8,
)


def main() -> None:
    ensure_python()
    require_git()
    root = demo_root()
    bob = root / "workspaces" / "bob"
    if not bob.is_dir():
        raise SystemExit("Run 01-scenario-A-duplicate-history.py first.")

    status = status_porcelain(bob)
    if not re.search(r"\b(UU|AA)\b", status) and "UU" not in status and "AA" not in status:
        print(
            "No merge conflict in progress. Re-run 01, then run this script while conflicts exist."
        )
        print("Or continue if you already merged - showing current graph:")
        show_graph(bob, "Current Bob history")
        return

    print("Resolving conflicts the 'normal' way (keep all features)...")
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
    run_git(
        "commit",
        "-m",
        "merge: resolve after public rebase (WRONG - pollutes history)",
        cwd=bob,
        check=True,
    )

    show_graph(bob, "After conventional conflict resolve")
    print()
    print("Duplicate commits (same message, different SHA):")
    proc1 = run_git("log", "--oneline", "--all", "--grep=add login", cwd=bob)
    proc2 = run_git("log", "--oneline", "--all", "--grep=send_message", cwd=bob)
    print(proc1.stdout or "", end="")
    print(proc2.stdout or "", end="")

    print()
    print("Why conventional cleanup fails:")
    print("  - git pull / merge: already done; history still has TWO copies of each patch")
    print("  - git rebase: will replay duplicates again, more conflicts")
    print("  - reverting the merge: still leaves both sides' commits in reachable history")
    print("  - only history rewrite (rebase -i / reset + cherry-pick) can clean")
    print()
    print("Code looks fine; the repository is not. This is the public-rebase tax.")


if __name__ == "__main__":
    main()
