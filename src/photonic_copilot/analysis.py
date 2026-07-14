"""Solver-independent numerical checks and validation report construction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np


CANONICAL_FIELDS = (
    "frequency",
    "wavelength",
    "reflectance",
    "transmittance",
    "absorption",
    "field_e",
    "field_h",
    "mode_coefficients",
    "q_factor",
    "far_field",
)


def load_arrays(path: Path) -> dict[str, np.ndarray]:
    suffix = path.suffix.lower()
    if suffix == ".npz":
        with np.load(path, allow_pickle=False) as data:
            return {key: np.asarray(data[key]) for key in data.files}
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {
            key: array
            for key, value in payload.items()
            if (array := np.asarray(value)).dtype.kind in "biufc"
        }
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
            raise ValueError("CSV must contain a named header row")
        return {
            key: np.atleast_1d(table[key])
            for key in table.dtype.names
            if np.atleast_1d(table[key]).dtype.kind in "biufc"
        }
    raise ValueError(f"unsupported result format: {path.suffix}")


def apply_field_map(
    arrays: Mapping[str, np.ndarray], field_map: Mapping[str, str] | None = None
) -> dict[str, np.ndarray]:
    mapped: dict[str, np.ndarray] = {}
    for source, value in arrays.items():
        target = (field_map or {}).get(source, source)
        if target in mapped:
            raise ValueError(f"field mapping creates duplicate key: {target}")
        mapped[target] = np.asarray(value)
    return mapped


def relative_change(current: np.ndarray, previous: np.ndarray) -> float:
    if current.shape != previous.shape:
        raise ValueError(f"shape mismatch: {current.shape} != {previous.shape}")
    numerator = float(np.linalg.norm(current - previous))
    denominator = max(float(np.linalg.norm(current)), np.finfo(float).tiny)
    return numerator / denominator


def validate_arrays(
    current: Mapping[str, np.ndarray],
    *,
    previous: Mapping[str, np.ndarray] | None = None,
    compare_keys: tuple[str, ...] = (),
    convergence_tolerance: float | None = None,
    rt_tolerance: float | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    if not current:
        failures.append("result contains no numeric arrays")
    for key, value in current.items():
        passed = bool(np.all(np.isfinite(value)))
        checks.append({"check": "finite", "key": key, "passed": passed})
        if not passed:
            failures.append(f"{key} contains NaN or Inf")

    for axis_key in ("frequency", "wavelength"):
        if axis_key not in current:
            continue
        values = np.ravel(current[axis_key])
        differences = np.diff(values)
        passed = bool(
            values.size > 0
            and np.all(np.isfinite(values))
            and np.all(values > 0)
            and (
                values.size == 1
                or np.all(differences > 0)
                or np.all(differences < 0)
            )
        )
        checks.append({"check": f"{axis_key}_axis", "passed": passed})
        if not passed:
            failures.append(f"{axis_key} must be finite, positive, and monotonic")

    if rt_tolerance is not None:
        if "reflectance" not in current or "transmittance" not in current:
            failures.append("R/T check requested but canonical fields are missing")
        else:
            residual = np.abs(
                1.0 - current["reflectance"] - current["transmittance"]
            )
            worst = float(np.max(residual))
            passed = worst <= rt_tolerance
            checks.append(
                {
                    "check": "lossless_rt_balance",
                    "worst_absolute_error": worst,
                    "tolerance": rt_tolerance,
                    "passed": passed,
                }
            )
            if not passed:
                failures.append(
                    f"R+T balance error {worst:.6g} exceeds {rt_tolerance:.6g}"
                )

    worst_relative: float | None = None
    if previous is not None:
        keys = compare_keys or tuple(
            sorted(
                key
                for key in current.keys() & previous.keys()
                if key not in {"frequency", "wavelength"}
            )
        )
        if not keys:
            failures.append("no common convergence arrays to compare")
        for key in keys:
            if key not in current or key not in previous:
                failures.append(f"convergence key missing from one case: {key}")
                continue
            change = relative_change(current[key], previous[key])
            worst_relative = max(worst_relative or 0.0, change)
            passed = convergence_tolerance is None or change <= convergence_tolerance
            checks.append(
                {
                    "check": "relative_change",
                    "key": key,
                    "value": change,
                    "tolerance": convergence_tolerance,
                    "passed": passed,
                }
            )
            if not passed:
                failures.append(
                    f"{key} relative change {change:.6g} exceeds "
                    f"{convergence_tolerance:.6g}"
                )

    return {
        "passed": not failures,
        "checks": checks,
        "failures": failures,
        "worst_relative_difference": worst_relative,
    }


def build_validation_report(
    *,
    run_id: str,
    raw_report: Mapping[str, Any],
    convergence_performed: bool,
    user_choice: str,
    proposed_cases: list[dict[str, Any]],
) -> dict[str, Any]:
    passed = bool(raw_report["passed"])
    completion_state = (
        "validated" if convergence_performed and passed else "executed"
    )
    checks = [
        {
            "name": check["check"],
            "method": "deterministic_python",
            "passed": bool(check["passed"]),
            "threshold": check.get("tolerance"),
            "value": check.get("value", check.get("worst_absolute_error")),
            "input_refs": [],
            "details": {
                key: value
                for key, value in check.items()
                if key
                not in {
                    "check",
                    "passed",
                    "tolerance",
                    "value",
                    "worst_absolute_error",
                }
            },
        }
        for check in raw_report["checks"]
    ]
    return {
        "schema_id": "ValidationReport",
        "schema_version": "1.0",
        "validation_id": f"validation-{run_id}",
        "run_id": run_id,
        "completion_state": completion_state,
        "convergence": {
            "performed": convergence_performed,
            "user_choice": user_choice,
            "proposed_cases": proposed_cases,
            "executed_cases": [],
            "worst_relative_difference": raw_report.get(
                "worst_relative_difference"
            ),
        },
        "checks": checks,
        "passed": passed,
        "warnings": list(raw_report.get("failures", [])),
        "limitations": (
            [] if convergence_performed else ["convergence not performed by user choice"]
        ),
    }
