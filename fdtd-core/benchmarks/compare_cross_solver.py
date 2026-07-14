"""Compare canonical Meep and Lumerical spectra without demanding equality."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from photonic_copilot.analysis import load_arrays, validate_arrays


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("meep", type=Path)
    parser.add_argument("lumerical", type=Path)
    parser.add_argument("--minimum-correlation", type=float, default=0.8)
    parser.add_argument("--rt-tolerance", type=float, default=0.05)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def _axis(data: dict[str, np.ndarray]) -> np.ndarray:
    if "wavelength" in data:
        return np.asarray(data["wavelength"], dtype=float).ravel()
    if "frequency" in data:
        return 1.0 / np.asarray(data["frequency"], dtype=float).ravel()
    raise ValueError("wavelength or frequency is required")


def _resample(
    axis: np.ndarray, values: np.ndarray, common: np.ndarray
) -> np.ndarray:
    order = np.argsort(axis)
    return np.interp(common, axis[order], np.asarray(values).ravel()[order])


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    if np.allclose(left, left[0]) and np.allclose(right, right[0]):
        return 1.0 if np.allclose(left, right) else 0.0
    value = np.corrcoef(left, right)[0, 1]
    return float(value) if np.isfinite(value) else 0.0


def compare(
    meep: dict[str, np.ndarray],
    lumerical: dict[str, np.ndarray],
    *,
    minimum_correlation: float,
    rt_tolerance: float,
) -> dict[str, Any]:
    required = {"reflectance", "transmittance"}
    for name, data in (("meep", meep), ("lumerical", lumerical)):
        missing = required - data.keys()
        if missing:
            raise ValueError(f"{name} is missing canonical fields: {sorted(missing)}")

    meep_axis = _axis(meep)
    lum_axis = _axis(lumerical)
    lower = max(float(np.min(meep_axis)), float(np.min(lum_axis)))
    upper = min(float(np.max(meep_axis)), float(np.max(lum_axis)))
    if not lower < upper:
        raise ValueError("solver wavelength ranges do not overlap")
    common = np.linspace(lower, upper, 200)

    checks: list[dict[str, Any]] = []
    for field in ("reflectance", "transmittance"):
        left = _resample(meep_axis, meep[field], common)
        right = _resample(lum_axis, lumerical[field], common)
        correlation = _correlation(left, right)
        checks.append(
            {
                "check": f"{field}_trend_correlation",
                "value": correlation,
                "threshold": minimum_correlation,
                "passed": correlation >= minimum_correlation,
            }
        )

    for name, data in (("meep", meep), ("lumerical", lumerical)):
        raw = validate_arrays(data, rt_tolerance=rt_tolerance)
        checks.append(
            {
                "check": f"{name}_self_validation",
                "passed": raw["passed"],
                "failures": raw["failures"],
            }
        )
    return {
        "passed": all(check["passed"] for check in checks),
        "comparison": "spectral trends and per-solver physics checks",
        "pointwise_equality_required": False,
        "common_wavelength_range": [lower, upper],
        "checks": checks,
    }


def main() -> int:
    args = parse_args()
    try:
        report = compare(
            load_arrays(args.meep),
            load_arrays(args.lumerical),
            minimum_correlation=args.minimum_correlation,
            rt_tolerance=args.rt_tolerance,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
