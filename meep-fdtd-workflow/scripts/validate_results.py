"""Generic finite-value, R/T-balance, and convergence checks for Meep output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path, help="NPZ or top-level numeric JSON")
    parser.add_argument("--previous", type=Path, help="previous convergence case")
    parser.add_argument(
        "--compare-key", action="append", default=[], help="array key to compare"
    )
    parser.add_argument("--convergence-tolerance", type=float)
    parser.add_argument(
        "--rt-tolerance",
        type=float,
        help="enable lossless R+T balance check with this absolute tolerance",
    )
    parser.add_argument("--report", type=Path, help="optional validation JSON")
    return parser.parse_args()


def load_arrays(path: Path) -> dict[str, np.ndarray]:
    if path.suffix.lower() == ".npz":
        with np.load(path, allow_pickle=False) as data:
            return {key: np.asarray(data[key]) for key in data.files}
    if path.suffix.lower() == ".json":
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        arrays: dict[str, np.ndarray] = {}
        for key, value in payload.items():
            try:
                array = np.asarray(value)
                if array.dtype.kind in "biufc":
                    arrays[key] = array
            except (TypeError, ValueError):
                continue
        return arrays
    raise ValueError(f"unsupported result format: {path.suffix}")


def relative_change(current: np.ndarray, previous: np.ndarray) -> float:
    if current.shape != previous.shape:
        raise ValueError(f"shape mismatch: {current.shape} != {previous.shape}")
    numerator = float(np.linalg.norm(current - previous))
    denominator = max(float(np.linalg.norm(current)), np.finfo(float).tiny)
    return numerator / denominator


def main() -> int:
    args = parse_args()
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    try:
        current = load_arrays(args.result)
    except Exception as exc:
        print(f"ERROR: cannot load {args.result}: {exc}")
        return 2

    if not current:
        failures.append("result contains no numeric arrays")

    for key, value in current.items():
        finite = bool(np.all(np.isfinite(value)))
        checks.append({"check": "finite", "key": key, "passed": finite})
        if not finite:
            failures.append(f"{key} contains NaN or Inf")

    if "frequency" in current:
        frequency = np.ravel(current["frequency"])
        valid_frequency = bool(
            frequency.size > 0
            and np.all(frequency > 0)
            and np.all(np.diff(frequency) > 0)
        )
        checks.append({"check": "frequency_axis", "passed": valid_frequency})
        if not valid_frequency:
            failures.append("frequency must be positive and strictly increasing")

    if args.rt_tolerance is not None:
        if "reflectance" not in current or "transmittance" not in current:
            failures.append("R/T check requested but reflectance/transmittance missing")
        else:
            residual = np.abs(
                1.0 - current["reflectance"] - current["transmittance"]
            )
            worst = float(np.max(residual))
            passed = worst <= args.rt_tolerance
            checks.append(
                {
                    "check": "lossless_rt_balance",
                    "worst_absolute_error": worst,
                    "tolerance": args.rt_tolerance,
                    "passed": passed,
                }
            )
            if not passed:
                failures.append(
                    f"R+T balance error {worst:.6g} exceeds {args.rt_tolerance:.6g}"
                )

    if args.previous:
        try:
            previous = load_arrays(args.previous)
            keys = args.compare_key or sorted(
                key
                for key in current.keys() & previous.keys()
                if key not in {"frequency", "wavelength"}
            )
            if not keys:
                failures.append("no common convergence arrays to compare")
            for key in keys:
                change = relative_change(current[key], previous[key])
                passed = (
                    args.convergence_tolerance is None
                    or change <= args.convergence_tolerance
                )
                checks.append(
                    {
                        "check": "relative_change",
                        "key": key,
                        "value": change,
                        "tolerance": args.convergence_tolerance,
                        "passed": passed,
                    }
                )
                if not passed:
                    failures.append(
                        f"{key} relative change {change:.6g} exceeds "
                        f"{args.convergence_tolerance:.6g}"
                    )
        except Exception as exc:
            failures.append(f"convergence comparison failed: {exc}")

    report = {
        "passed": not failures,
        "result": str(args.result),
        "previous": str(args.previous) if args.previous else None,
        "checks": checks,
        "failures": failures,
    }
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
