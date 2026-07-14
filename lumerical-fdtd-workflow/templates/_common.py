"""Shared helpers for reviewed Lumerical Python templates."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np


def import_lumerical_api(api_path: Path | None = None) -> tuple[ModuleType, str]:
    if api_path is not None:
        import sys

        sys.path.insert(0, str(api_path.expanduser().resolve()))
    failures: list[str] = []
    for module_name, flavor in (
        ("ansys.lumerical.core", "ansys.lumerical.core"),
        ("lumapi", "traditional lumapi"),
    ):
        try:
            return importlib.import_module(module_name), flavor
        except Exception as exc:
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")
    raise RuntimeError("No supported Lumerical API could be imported; " + "; ".join(failures))


def close_session(session: Any) -> None:
    close = getattr(session, "close", None)
    if callable(close):
        close()


def dataset_array(dataset: Any, *keys: str) -> np.ndarray:
    for key in keys:
        try:
            value = dataset[key]
        except (KeyError, TypeError, IndexError):
            value = getattr(dataset, key, None)
        if value is not None:
            return np.asarray(value).squeeze()
    raise KeyError(f"none of the result fields exist: {keys}")


def write_metadata(output: Path, payload: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "metadata.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def base_metadata(
    *,
    template_id: str,
    api_flavor: str | None,
    completion_state: str,
    projects: list[str],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    return {
        "template_id": template_id,
        "template_version": "1.0.0",
        "solver": "lumerical-fdtd",
        "api_flavor": api_flavor,
        "completion_state": completion_state,
        "projects": projects,
        "parameters_si": parameters,
        "convergence_plan": {
            "independent_variables": [
                "mesh_accuracy_or_local_mesh",
                "pml_layers_and_padding",
                "simulation_time_and_auto_shutoff",
            ],
            "performed": False,
        },
        "warnings": [],
    }
