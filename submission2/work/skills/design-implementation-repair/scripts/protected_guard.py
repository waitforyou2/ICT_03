#!/usr/bin/env python3
"""Snapshot and verify competition inputs that a repair must not modify."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


EXCLUDED_PARTS = {"target", ".git", ".codegraph", "maven-repo", "validation"}
ROOT_FILE_NAMES = {
    "README.md",
    "PLATFORM.md",
    "maven-settings.xml",
    "蓝区README.md",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_generated(path: Path, root: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts)


def protected_files(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for name in ROOT_FILE_NAMES:
        candidate = root / name
        if candidate.is_file():
            paths.add(candidate)

    design = root / "design-docs"
    if design.is_dir():
        paths.update(path for path in design.rglob("*") if path.is_file())

    tests = root / "test-cases"
    if tests.is_dir():
        paths.update(
            path for path in tests.rglob("*")
            if path.is_file() and not is_generated(path, root)
        )
    return sorted(paths)


def build_snapshot(root: Path) -> dict:
    entries = []
    for path in protected_files(root):
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return {
        "schema_version": "1.0",
        "asset_root": str(root),
        "files": entries,
    }


def compare(root: Path, snapshot: dict) -> dict:
    expected = {entry["path"]: entry for entry in snapshot.get("files", [])}
    current_paths = {
        path.relative_to(root).as_posix(): path for path in protected_files(root)
    }
    added = sorted(set(current_paths) - set(expected))
    deleted = sorted(set(expected) - set(current_paths))
    modified = []
    for relative in sorted(set(expected) & set(current_paths)):
        path = current_paths[relative]
        if sha256(path) != expected[relative].get("sha256"):
            modified.append(relative)
    return {
        "passed": not (added or deleted or modified),
        "added": added,
        "deleted": deleted,
        "modified": modified,
        "checked": len(expected),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot")
    snapshot.add_argument("--assets", required=True, type=Path)
    snapshot.add_argument("--output", required=True, type=Path)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--assets", required=True, type=Path)
    verify.add_argument("--snapshot", required=True, type=Path)
    verify.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.assets.resolve()
    if not root.is_dir():
        raise SystemExit(f"Asset root does not exist: {root}")

    if args.command == "snapshot":
        payload = build_snapshot(root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"PROTECTED_SNAPSHOT files={len(payload['files'])} output={args.output}")
        return 0

    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    result = compare(root, snapshot)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
