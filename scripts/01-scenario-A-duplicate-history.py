#!/usr/bin/env python3
"""Scenario A: rebase + force-push on public feature -> peer pull conflict / duplicates.

Usage:
  python scripts/01-scenario-A-duplicate-history.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    demo_root,
    ensure_python,
    git_out,
    init_bare,
    init_clone,
    rebase_in_progress,
    require_git,
    reset_dir,
    run_git,
    show_graph,
    write_json,
    write_utf8,
)


def main() -> None:
    ensure_python()
    require_git()
    root = demo_root()
    ws = root / "workspaces"
    reset_dir(ws)

    remote = ws / "origin.git"
    alice = ws / "alice"
    bob = ws / "bob"

    init_bare(remote)
    init_clone(remote, alice, "Alice", "alice@example.com")
    init_clone(remote, bob, "Bob", "bob@example.com")

    # --- healthy shared history ---
    write_utf8(
        alice / "README.md",
        "# Team Chat\n\nshared baseline\n",
    )
    write_utf8(
        alice / "app.py",
        "VERSION = '0.1'\n\n"
        "def greet(name):\n"
        "    return f'Hello, {name}'\n",
    )

    # Empty bare has no origin/main yet → create local main, then push
    run_git("switch", "-c", "main", cwd=alice, check=True)
    run_git("add", ".", cwd=alice, check=True)
    run_git("commit", "-m", "init: shared baseline", cwd=alice, check=True)
    run_git("push", "-u", "origin", "main", cwd=alice, check=True)

    run_git("switch", "-c", "feature", cwd=alice, check=True)
    run_git("push", "-u", "origin", "feature", cwd=alice, check=True)

    write_utf8(
        alice / "README.md",
        "# Team Chat\n\n- login\n",
    )
    write_utf8(
        alice / "app.py",
        "VERSION = '0.1'\n\n"
        "def greet(name):\n"
        "    return f'Hello, {name}'\n\n"
        "def login(user, password):\n"
        "    return user == 'admin' and password == 'secret'\n",
    )
    run_git("add", ".", cwd=alice, check=True)
    run_git("commit", "-m", "feat(feature): add login (Alice)", cwd=alice, check=True)
    run_git("push", "origin", "feature", cwd=alice, check=True)

    run_git("fetch", cwd=bob, check=True)
    run_git("switch", "feature", cwd=bob, check=True)
    run_git("pull", "origin", "feature", cwd=bob, check=True)

    write_utf8(
        bob / "README.md",
        "# Team Chat\n\n- login\n- messages\n",
    )
    write_utf8(
        bob / "app.py",
        "VERSION = '0.1'\n\n"
        "def greet(name):\n"
        "    return f'Hello, {name}'\n\n"
        "def login(user, password):\n"
        "    return user == 'admin' and password == 'secret'\n\n"
        "def send_message(user, text):\n"
        "    return f'{user}: {text}'\n",
    )
    run_git("add", ".", cwd=bob, check=True)
    run_git("commit", "-m", "feat(feature): add send_message (Bob)", cwd=bob, check=True)
    run_git("push", "origin", "feature", cwd=bob, check=True)

    run_git("pull", "origin", "feature", cwd=alice, check=True)
    old_tip = git_out("rev-parse", "--short", "HEAD", cwd=alice)
    show_graph(alice, "HEALTHY shared feature (both in sync)")

    # --- main advances ---
    run_git("switch", "main", cwd=alice, check=True)
    write_utf8(
        alice / "README.md",
        "# Team Chat\n\nshared baseline\n- security patch on main\n",
    )
    write_utf8(
        alice / "app.py",
        "VERSION = '0.2'\n\n"
        "def greet(name):\n"
        "    return f'Hello, {name}!'\n",
    )
    run_git("add", ".", cwd=alice, check=True)
    run_git("commit", "-m", "fix(main): security patch + version bump", cwd=alice, check=True)
    run_git("push", "origin", "main", cwd=alice, check=True)

    # --- Bob local WIP on old feature (not pushed) ---
    run_git("switch", "feature", cwd=bob, check=True)
    write_utf8(
        bob / "README.md",
        "# Team Chat\n\n"
        "- login\n"
        "- messages\n"
        "- emoji reactions (Bob WIP)\n",
    )
    write_utf8(
        bob / "app.py",
        "VERSION = '0.1'\n\n"
        "def greet(name):\n"
        "    return f'Hello, {name}'\n\n"
        "def login(user, password):\n"
        "    return user == 'admin' and password == 'secret'\n\n"
        "def send_message(user, text):\n"
        "    return f'{user}: {text}'\n\n"
        "def add_reaction(msg, emoji):\n"
        "    return f'{msg} {emoji}'\n",
    )
    run_git("add", ".", cwd=bob, check=True)
    run_git("commit", "-m", "feat(feature): add emoji reactions (Bob local)", cwd=bob, check=True)
    bob_only = git_out("rev-parse", "--short", "HEAD", cwd=bob)
    print(f"Bob-only local commit: {bob_only} (based on old tip {old_tip})")

    # --- Alice rebases public feature and force-pushes ---
    run_git("switch", "feature", cwd=alice, check=True)
    run_git("fetch", "origin", cwd=alice, check=True)

    rebase = run_git("rebase", "origin/main", cwd=alice, check=False)
    if rebase.returncode != 0 or rebase_in_progress(alice):
        write_utf8(
            alice / "README.md",
            "# Team Chat\n\n- security patch on main\n- login\n",
        )
        write_utf8(
            alice / "app.py",
            "VERSION = '0.2'\n\n"
            "def greet(name):\n"
            "    return f'Hello, {name}!'\n\n"
            "def login(user, password):\n"
            "    return user == 'admin' and password == 'secret'\n",
        )
        run_git("add", "README.md", "app.py", cwd=alice, check=True)
        run_git("rebase", "--continue", cwd=alice, check=False)
        while rebase_in_progress(alice):
            write_utf8(
                alice / "README.md",
                "# Team Chat\n\n"
                "- security patch on main\n"
                "- login\n"
                "- messages\n",
            )
            write_utf8(
                alice / "app.py",
                "VERSION = '0.2'\n\n"
                "def greet(name):\n"
                "    return f'Hello, {name}!'\n\n"
                "def login(user, password):\n"
                "    return user == 'admin' and password == 'secret'\n\n"
                "def send_message(user, text):\n"
                "    return f'{user}: {text}'\n",
            )
            run_git("add", "README.md", "app.py", cwd=alice, check=True)
            run_git("rebase", "--continue", cwd=alice, check=False)

    show_graph(alice, "Alice after rebase (SAME messages, NEW hashes, NEW parents)")
    run_git("push", "--force-with-lease", "origin", "feature", cwd=alice, check=True)
    print("Alice force-pushed rewritten PUBLIC feature.")

    # --- Bob conventional pull (3-way merge) ---
    print()
    print("Bob runs: git pull origin feature   # default = 3-way merge")
    run_git("fetch", "origin", cwd=bob, check=True)
    pull = run_git("pull", "origin", "feature", "--no-edit", cwd=bob, check=False)
    if pull.stdout:
        print(pull.stdout, end="")
    if pull.stderr:
        print(pull.stderr, end="")

    show_graph(bob, "Bob AFTER conventional pull (diverged / conflicted)")
    print()
    print("STATE READY FOR HANDS-ON:")
    print("  cd workspaces/bob")
    print("  inspect conflicts: cat README.md; cat app.py   (Windows: type README.md)")
    print("  diverged history: old SHAs vs new SHAs")
    print(f"  old tip (pre-rebase shared): {old_tip}")
    print(f"  Bob-only commit: {bob_only}")
    print()
    print("Next:")
    print("  1) conventional conflict resolve -> python scripts/02-wrong-merge-resolve.py")
    print("  2) or abort + proper recovery -> python scripts/03-proper-recovery-onto.py")

    write_json(
        ws / "scenario-A-meta.json",
        {
            "oldTip": old_tip,
            "bobOnly": bob_only,
            "alice": str(alice),
            "bob": str(bob),
            "remote": str(remote),
        },
    )


if __name__ == "__main__":
    main()
