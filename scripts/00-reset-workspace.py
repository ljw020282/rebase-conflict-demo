#!/usr/bin/env python3
"""Reset workspaces/: bare origin + Alice/Bob clones for manual step-by-step practice.

Usage:
  python scripts/00-reset-workspace.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    demo_root,
    ensure_python,
    init_bare,
    init_clone,
    require_git,
    reset_dir,
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
    # git init --bare -b main workspaces/origin.git
    init_bare(remote)

    # git clone /workspaces/origin.git /workspaces/alice
    # git -C config user.name Alice
    # git -C config user.email alice@example.com
    init_clone(remote, alice, "Alice", "alice@example.com")
    
    # git clone /workspaces/origin.git /workspaces/bob
    # git -C config user.name Bob
    # git -C config user.email bob@example.com
    init_clone(remote, bob, "Bob", "bob@example.com")
    print(f"Ready: {ws}")
    print("  origin.git / alice / bob")


if __name__ == "__main__":
    main()
