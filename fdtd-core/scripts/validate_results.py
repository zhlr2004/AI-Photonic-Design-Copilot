"""CLI for solver-independent FDTD result checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from photonic_copilot.analysis import apply_field_map, load_arrays, validate_arrays


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--compare-key", action="append", default=[])
    parser.add_argument("--field-map", action="append", default=[])
    parser.add_argument("--convergence-tolerance", type=float)
    parser.add_argument("--rt-tolerance", type=float)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def parse_field_map(items: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in items:
        source, separator, canonical = item.partition("=")
        if not separator or not source.strip() or not canonical.strip():
            raise ValueError(f"invalid field map {item!r}; expected SOURCE=CANONICAL")
        mapping[source.strip()] = canonical.strip()
    return mapping


def main() -> int:
    args = parse_args()
    if args.convergence_tolerance is not None and args.convergence_tolerance < 0:
        raise SystemExit("--convergence-tolerance must be nonnegative")
    if args.rt_tolerance is not None and args.rt_tolerance < 0:
        raise SystemExit("--rt-tolerance must be nonnegative")

    try:
        field_map = parse_field_map(args.field_map)
        current = apply_field_map(load_arrays(args.result), field_map)
        previous = (
            apply_field_map(load_arrays(args.previous), field_map)
            if args.previous
            else None
        )
        report = validate_arrays(
            current,
            previous=previous,
            compare_keys=tuple(args.compare_key),
            convergence_tolerance=args.convergence_tolerance,
            rt_tolerance=args.rt_tolerance,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2

    report["result"] = str(args.result)
    report["previous"] = str(args.previous) if args.previous else None
    report["field_map"] = field_map
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
