"""Publish a staged case with a human G3 decision bound to its candidate hash."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from photonic_copilot.folder_example_library import FolderExampleLibrary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--validation-report", type=Path)
    parser.add_argument("--library-root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        decision = json.loads(args.decision.read_text(encoding="utf-8"))
        validation = (
            json.loads(args.validation_report.read_text(encoding="utf-8"))
            if args.validation_report
            else None
        )
        library = FolderExampleLibrary(args.library_root)
        manifest = library.publish_reviewed(
            args.candidate_id,
            decision=decision,
            validation_report=validation,
        )
        print(
            json.dumps(
                {
                    "state": "published",
                    "example_id": manifest["example_id"],
                    "version": manifest["version"],
                    "quality": manifest["quality"],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
