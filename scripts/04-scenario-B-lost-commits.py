#!/usr/bin/env python3
"""Scenario B: rebase stale public branch + --force drops others' pushed commits.

Usage:
  python scripts/04-scenario-B-lost-commits.py
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
    write_utf8,
)


def main() -> None:
    ensure_python()
    require_git()
    root = demo_root()
    ws = root / "workspaces-lost"
    reset_dir(ws)

    remote = ws / "origin.git"
    alice = ws / "alice"
    bob = ws / "bob"

    init_bare(remote)
    init_clone(remote, alice, "Alice", "alice@example.com")
    init_clone(remote, bob, "Bob", "bob@example.com")

    write_utf8(alice / "note.txt", "base\n")
    run_git("switch", "-c", "main", cwd=alice, check=True)
    run_git("add", ".", cwd=alice, check=True)
    run_git("commit", "-m", "init", cwd=alice, check=True)
    run_git("switch", "-c", "feature", cwd=alice, check=True)
    write_utf8(alice / "note.txt", "alice-1\n")
    run_git("add", ".", cwd=alice, check=True)
    run_git("commit", "-m", "feat: Alice work A1", cwd=alice, check=True)
    run_git("push", "-u", "origin", "main", cwd=alice, check=True)
    run_git("push", "-u", "origin", "feature", cwd=alice, check=True)

    run_git("fetch", cwd=bob, check=True)
    run_git("switch", "feature", cwd=bob, check=True)
    write_utf8(bob / "note.txt", "alice-1\nbob-1 CRITICAL\n")
    run_git("add", ".", cwd=bob, check=True)
    run_git("commit", "-m", "feat: Bob CRITICAL fix B1 (already pushed)", cwd=bob, check=True)
    run_git("push", "origin", "feature", cwd=bob, check=True)
    bob_sha = git_out("rev-parse", "HEAD", cwd=bob)
    bob_short = git_out("rev-parse", "--short", "HEAD", cwd=bob)
    print(f"Bob pushed CRITICAL commit {bob_short} to PUBLIC feature")

    # Alice never fetches; local feature still at A1
    run_git("switch", "main", cwd=alice, check=True)
    write_utf8(alice / "note.txt", "base\nmain-hotfix\n")
    run_git("add", ".", cwd=alice, check=True)
    run_git("commit", "-m", "fix(main): hotfix", cwd=alice, check=True)
    run_git("push", "origin", "main", cwd=alice, check=True)

    run_git("switch", "feature", cwd=alice, check=True)
    print("Alice local feature is STALE (never fetched Bob):")
    print(run_git("log", "--oneline", "-3", cwd=alice).stdout or "", end="")

    run_git("rebase", "main", cwd=alice, check=False)
    if rebase_in_progress(alice):
        write_utf8(alice / "note.txt", "base\nmain-hotfix\nalice-1-rebased\n")
        run_git("add", "note.txt", cwd=alice, check=True)
        run_git("rebase", "--continue", cwd=alice, check=False)

    show_graph(alice, "Alice rebased stale feature (Bob commit never included)")

    print()
    print("Trying --force-with-lease (safer): should REJECT because remote moved...")
    lease = run_git("push", "--force-with-lease", "origin", "feature", cwd=alice, check=False)
    print((lease.stdout or "") + (lease.stderr or ""), end="")
    if lease.returncode == 0:
        print("Unexpected: lease allowed push. Check fetch state.")
    else:
        print("Good: --force-with-lease blocked the overwrite.")

    print()
    print("Alice ignores safety and uses --force ...")
    force = run_git("push", "--force", "origin", "feature", cwd=alice, check=False)
    print((force.stdout or "") + (force.stderr or ""), end="")

    print("Remote feature tip now:")
    print(
        run_git("log", "--oneline", "feature", "-5", git_dir=remote).stdout or "",
        end="",
    )

    contains = git_out("branch", "--contains", bob_sha, git_dir=remote)
    print(f"Branches containing Bob CRITICAL ({bob_short}): '{contains}'")
    if not contains.strip():
        print(
            "UNREACHABLE from any branch tip on remote. "
            "Object may linger until GC; teammates who never fetched can LOSE it forever."
        )

    print()
    print("Bob still has it locally:")
    print(run_git("log", "--oneline", "-3", cwd=bob).stdout or "", end="")
    print(
        "Conventional 'git pull' on Alice machine will NOT bring B1 back - "
        "it was never in her rewritten history."
    )
    print(
        f"Recovery requires: someone who still has {bob_short} "
        "(Bob reflog / local) to cherry-pick or push it again."
    )
    print()
    print("Hands-on: cd workspaces-lost/bob and try to re-publish CRITICAL.")


if __name__ == "__main__":
    main()
