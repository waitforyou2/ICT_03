from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .engine import analyze


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="specdiff", description="Audit implementation against design documents")
    result.add_argument("--version", action="version", version=__version__)
    commands = result.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("analyze", help="run an unattended audit")
    audit.add_argument("--repo", required=True, help="source repository/directory")
    audit.add_argument("--docs", required=True, help="design document file/directory")
    audit.add_argument("--output", required=True, help="result directory")
    audit.add_argument("--cache", default=str(Path(__file__).resolve().parents[1] / "cache"))
    audit.add_argument("--offline", action="store_true", help="use only cached documents")
    audit.add_argument("--codegraph", choices=("auto", "off", "required"), default="required")
    audit.add_argument("--codegraph-bin")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        summary, findings = analyze(
            args.repo, args.docs, args.output, args.cache,
            allow_network=not args.offline, codegraph=args.codegraph,
            codegraph_bin=args.codegraph_bin,
        )
    except Exception as exc:  # noqa: BLE001 - CLI must return a deterministic status
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"status": summary.status, "findings": len(findings), "output": str(Path(args.output).resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
