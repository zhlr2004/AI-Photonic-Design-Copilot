"""Scan staged text for credentials and required machine-specific paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from photonic_copilot.curation import scan_sensitive


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = args.candidate_dir / "payload"
        report = scan_sensitive(payload)
        rendered = json.dumps(report, indent=2, ensure_ascii=False)
        print(rendered)
        target = args.report or args.candidate_dir / "sensitivity-report.json"
        target.write_text(rendered + "\n", encoding="utf-8")
        return 0 if report["passed"] else 4
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
