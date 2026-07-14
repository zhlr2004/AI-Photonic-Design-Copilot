"""Validate portable numerical output from a Lumerical FDTD workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check NPZ, top-level numeric JSON, or headered numeric CSV data."
    )
    parser.add_argument("result", type=Path)
    parser.add_argument("--previous", type=Path, help="previous convergence case")
    parser.add_argument(
        "--compare-key", action="append", default=[], help="canonical key to compare"
    )
    parser.add_argument(
        "--field-map",
        action="append",
        default=[],
        metavar="SOURCE=CANONICAL",
        help="rename an input field; repeat as needed (for example T=transmittance)",
    )
    parser.add_argument("--convergence-tolerance", type=float)
    parser.add_argument(
        "--rt-tolerance",
        type=float,
        help="enable lossless R+T balance with this absolute tolerance",
    )
    parser.add_argument("--report", type=Path, help="optional validation JSON")
    return parser.parse_args()


def load_arrays(path: Path) -> dict[str, np.ndarray]:
    suffix = path.suffix.lower()
    if suffix == ".npz":
        with np.load(path, allow_pickle=False) as data:
            return {key: np.asarray(data[key]) for key in data.files}

    if suffix == ".json":
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

    if suffix == ".csv":
        table = np.genfromtxt(
            path,
            delimiter=",",
            names=True,
            dtype=None,
            encoding="utf-8-sig",
            autostrip=True,
        )
        if table.dtype.names is None:
            raise ValueError("CSV must contain one header row with named columns")
        arrays = {}
        for key in table.dtype.names:
            column = np.atleast_1d(table[key])
            if column.dtype.kind in "biufc":
                arrays[key] = column
        return arrays

    raise ValueError(f"unsupported result format: {path.suffix}")


def parse_field_map(items: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in items:
        source, separator, canonical = item.partition("=")
        if not separator or not source.strip() or not canonical.strip():
            raise ValueError(f"invalid field map {item!r}; expected SOURCE=CANONICAL")
        mapping[source.strip()] = canonical.strip()
    return mapping


def apply_field_map(
    arrays: dict[str, np.ndarray], mapping: dict[str, str]
) -> dict[str, np.ndarray]:
    renamed: dict[str, np.ndarray] = {}
    for key, value in arrays.items():
        target = mapping.get(key, key)
        if target in renamed:
            raise ValueError(f"field mapping creates duplicate key: {target}")
        renamed[target] = value
    return renamed


def relative_change(current: np.ndarray, previous: np.ndarray) -> float:
    if current.shape != previous.shape:
        raise ValueError(f"shape mismatch: {current.shape} != {previous.shape}")
    numerator = float(np.linalg.norm(current - previous))
    denominator = max(float(np.linalg.norm(current)), np.finfo(float).tiny)
    return numerator / denominator


def monotonic_positive(axis: np.ndarray) -> bool:
    values = np.ravel(axis)
    if values.size == 0 or not np.all(np.isfinite(values)) or not np.all(values > 0):
        return False
    if values.size == 1:
        return True
    differences = np.diff(values)
    return bool(np.all(differences > 0) or np.all(differences < 0))


def main() -> int:
    args = parse_args()
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    if args.convergence_tolerance is not None and args.convergence_tolerance < 0:
        print("ERROR: --convergence-tolerance must be nonnegative")
        return 2
    if args.rt_tolerance is not None and args.rt_tolerance < 0:
        print("ERROR: --rt-tolerance must be nonnegative")
        return 2

    try:
        mapping = parse_field_map(args.field_map)
        current = apply_field_map(load_arrays(args.result), mapping)
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

    for axis_key in ("frequency", "wavelength"):
        if axis_key in current:
            passed = monotonic_positive(current[axis_key])
            checks.append({"check": f"{axis_key}_axis", "passed": passed})
            if not passed:
                failures.append(
                    f"{axis_key} must be finite, positive, and strictly monotonic"
                )

    if args.rt_tolerance is not None:
        if "reflectance" not in current or "transmittance" not in current:
            failures.append("R/T check requested but reflectance/transmittance missing")
        else:
            try:
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
                        f"R+T balance error {worst:.6g} exceeds "
                        f"{args.rt_tolerance:.6g}"
                    )
            except Exception as exc:
                failures.append(f"R/T balance check failed: {exc}")

    if args.previous:
        try:
            previous = apply_field_map(load_arrays(args.previous), mapping)
            keys = args.compare_key or sorted(
                key
                for key in current.keys() & previous.keys()
                if key not in {"frequency", "wavelength"}
            )
            if not keys:
                failures.append("no common convergence arrays to compare")
            for key in keys:
                if key not in current or key not in previous:
                    failures.append(f"convergence key missing from one case: {key}")
                    continue
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
        "field_map": mapping,
        "checks": checks,
        "failures": failures,
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
