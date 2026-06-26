#!/usr/bin/env python3
"""Re-vendor an Asymptote skill into the asyagent package.

Copies a skill source directory into ``asyagent/_skill/``, excluding build
artifacts and VCS cruft so the bundled copy stays clean. Run this after
updating the skill source, then commit the refreshed ``asyagent/_skill/``.

Pure standard library (matches asyagent's zero-dependency philosophy).

Usage:
    python3 scripts/vendor_skill.py [--src DIR] [--dst DIR]

Defaults:
    --src  ./asyagent/_skill        (the in-package skill source)
    --dst  ./asyagent/_skill        (same — a no-op self-refresh by default)

When importing a skill from elsewhere, pass ``--src /path/to/external/skill``.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Top-level names never copied into the vendored bundle.
EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", "vendor", "build", "dist"}
EXCLUDE_FILES = {".gitignore", ".gitattributes", ".DS_Store", "Thumbs.db"}
# Specific render-test artifacts that littered scripts/ historically.
EXCLUDE_FILE_STEMS = {"asy-output", "hello"}


def _should_skip(path: Path) -> bool:
    if path.name in EXCLUDE_DIRS or path.name in EXCLUDE_FILES:
        return True
    if path.suffix == ".svg" and path.stem in EXCLUDE_FILE_STEMS:
        return True
    if path.suffix == ".pyc":
        return True
    return False


def vendor(src: Path, dst: Path) -> int:
    if not src.is_dir():
        print(f"error: source skill dir not found: {src}", file=sys.stderr)
        return 1
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    count = 0
    for entry in sorted(src.rglob("*")):
        rel = entry.relative_to(src)
        # Skip if any path component is excluded.
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if _should_skip(entry):
            continue
        target = dst / rel
        if entry.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, target)
            count += 1
    print(f"vendored {count} files: {src} -> {dst}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--src",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "asyagent" / "_skill",
        help="source skill directory (default: ./asyagent/_skill)",
    )
    parser.add_argument(
        "--dst",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "asyagent" / "_skill",
        help="destination vendored directory (default: ./asyagent/_skill)",
    )
    args = parser.parse_args(argv)
    return vendor(args.src, args.dst)


if __name__ == "__main__":
    raise SystemExit(main())
