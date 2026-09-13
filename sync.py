#!/usr/bin/env python3
"""Keep the Claude and Codex copies of each skill's shared files identical.

Each version folder is self-contained so it can be symlinked into place on its
own, which means the scripts exist twice. Only the instruction file differs —
SKILL.md for Claude, AGENTS.md for Codex — so everything else is mirrored from
the Claude folder.

    ./sync.py            mirror claude/ -> codex/
    ./sync.py --check    exit non-zero if they have drifted (for CI or a hook)
"""

from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INSTRUCTIONS = {"SKILL.md", "AGENTS.md"}


def shared_files(src: Path):
    for f in sorted(src.rglob("*")):
        if f.is_file() and f.name not in INSTRUCTIONS and "__pycache__" not in f.parts:
            yield f


def main() -> None:
    check = "--check" in sys.argv
    drift, copied = [], []

    for skill in sorted(p for p in ROOT.iterdir() if (p / "claude").is_dir()):
        src, dst = skill / "claude", skill / "codex"
        for f in shared_files(src):
            target = dst / f.relative_to(src)
            same = target.is_file() and filecmp.cmp(f, target, shallow=False)
            if same:
                continue
            rel = target.relative_to(ROOT)
            if check:
                drift.append(str(rel))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
                copied.append(str(rel))

        # a file removed from claude/ should not linger in codex/
        keep = {str((dst / f.relative_to(src)).resolve()) for f in shared_files(src)}
        for f in shared_files(dst):
            if str(f.resolve()) in keep:
                continue
            rel = f.relative_to(ROOT)
            if check:
                drift.append(f"{rel} (stale)")
            else:
                f.unlink()
                copied.append(f"{rel} (removed)")

    if check:
        if drift:
            print("out of sync — run ./sync.py:", file=sys.stderr)
            for d in drift:
                print(f"  {d}", file=sys.stderr)
            raise SystemExit(1)
        print("in sync")
        return

    for c in copied:
        print(f"  {c}")
    print(f"synced {len(copied)} file(s)" if copied else "already in sync")


if __name__ == "__main__":
    main()
