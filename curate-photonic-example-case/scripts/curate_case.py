"""Inspect or prepare a legacy photonic case without modifying its source."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from photonic_copilot.curation import inspect_case, load_metadata, prepare_case
from photonic_copilot.folder_example_library import FolderExampleLibrary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "prepare"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--source", type=Path, required=True)
        sub.add_argument("--library-root", type=Path)
        sub.add_argument("--candidate-id", required=True)
        sub.add_argument(
            "--mode",
            choices=("paper_reproduction", "free_design"),
            required=True,
        )
        sub.add_argument("--target-version", default="1.0.0")
    prepare = subparsers.choices["prepare"]
    prepare.add_argument("--plan", type=Path, required=True)
    prepare.add_argument("--metadata", type=Path)
    prepare.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def render(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    args = parse_args()
    try:
        if args.command == "inspect":
            snapshot, report = inspect_case(
                args.source,
                candidate_id=args.candidate_id,
                mode=args.mode,
            )
            render({"source_snapshot": snapshot, "cleaning_plan": report})
            if report["blocked"]:
                return 4
            if report["required_questions"]:
                return 3
            return 0

        plan_payload = json.loads(args.plan.read_text(encoding="utf-8"))
        plan = plan_payload.get("cleaning_plan", plan_payload)
        if args.dry_run:
            snapshot, current = inspect_case(
                args.source,
                candidate_id=args.candidate_id,
                mode=args.mode,
            )
            render(
                {
                    "dry_run": True,
                    "source_snapshot": snapshot,
                    "plan_matches_source": (
                        snapshot["tree_sha256"]
                        == plan.get("source_snapshot_sha256")
                    ),
                    "blocked": current["blocked"],
                    "would_stage": args.candidate_id,
                }
            )
            return 4 if current["blocked"] else 0

        library = FolderExampleLibrary(args.library_root)
        staging = prepare_case(
            args.source,
            library=library,
            candidate_id=args.candidate_id,
            mode=args.mode,
            target_version=args.target_version,
            plan=plan,
            metadata=load_metadata(args.metadata),
        )
        candidate = json.loads(
            (staging / "example-candidate.json").read_text(encoding="utf-8")
        )
        render(
            {
                "state": "review_pending",
                "staging_dir": str(staging),
                "candidate_id": candidate["candidate_id"],
                "recommended_quality": candidate["manifest_draft"]["quality"],
            }
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
