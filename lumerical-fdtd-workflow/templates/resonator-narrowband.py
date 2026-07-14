"""Narrow-band 2D ring-resonator spectrum and loaded-Q estimate."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from _common import (
    base_metadata,
    close_session,
    dataset_array,
    import_lumerical_api,
    write_metadata,
)


TEMPLATE_ID = "lumerical-resonator-narrowband"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("results/resonator-narrowband")
    )
    parser.add_argument("--api-path", type=Path)
    parser.add_argument("--show-gui", action="store_true")
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mesh-accuracy", type=int, default=3)
    return parser.parse_args()


def parameters(mesh_accuracy: int) -> dict[str, float | int]:
    return {
        "wavelength_start_m": 1.50e-6,
        "wavelength_stop_m": 1.60e-6,
        "ring_outer_radius_m": 5.0e-6,
        "ring_width_m": 0.50e-6,
        "coupling_gap_m": 0.20e-6,
        "waveguide_width_m": 0.50e-6,
        "core_index": 3.45,
        "mesh_accuracy": mesh_accuracy,
        "simulation_time_s": 8.0e-12,
        "auto_shutoff_min": 1.0e-6,
    }


def build_model(fdtd: Any, p: dict[str, float | int]) -> None:
    radius = float(p["ring_outer_radius_m"])
    width = float(p["ring_width_m"])
    gap = float(p["coupling_gap_m"])
    bus_y = -(radius + 0.5 * width + gap)

    fdtd.addfdtd()
    fdtd.set("name", "fdtd")
    fdtd.set("dimension", "2D")
    fdtd.set("x span", 16.0e-6)
    fdtd.set("y span", 16.0e-6)
    fdtd.set("mesh accuracy", p["mesh_accuracy"])
    fdtd.set("simulation time", p["simulation_time_s"])
    fdtd.set("auto shutoff min", p["auto_shutoff_min"])
    for boundary in ("x min bc", "x max bc", "y min bc", "y max bc"):
        fdtd.set(boundary, "PML")

    fdtd.addring()
    fdtd.set("name", "ring")
    fdtd.set("outer radius", radius)
    fdtd.set("inner radius", radius - width)
    fdtd.set("index", p["core_index"])

    fdtd.addrect()
    fdtd.set("name", "bus_waveguide")
    fdtd.set("x span", 14.0e-6)
    fdtd.set("y", bus_y)
    fdtd.set("y span", p["waveguide_width_m"])
    fdtd.set("index", p["core_index"])

    fdtd.addmode()
    fdtd.set("name", "input_mode")
    fdtd.set("injection axis", "x-axis")
    fdtd.set("direction", "Forward")
    fdtd.set("x", -6.0e-6)
    fdtd.set("y", bus_y)
    fdtd.set("y span", 2.0e-6)
    fdtd.set("wavelength start", p["wavelength_start_m"])
    fdtd.set("wavelength stop", p["wavelength_stop_m"])
    fdtd.set("mode selection", "fundamental mode")

    fdtd.addpower()
    fdtd.set("name", "through_power")
    fdtd.set("monitor type", "2D X-normal")
    fdtd.set("x", 6.0e-6)
    fdtd.set("y", bus_y)
    fdtd.set("y span", 2.0e-6)


def loaded_q_from_dip(
    wavelength: np.ndarray, transmittance: np.ndarray
) -> tuple[float, float]:
    order = np.argsort(wavelength)
    wavelength = np.asarray(wavelength, dtype=float).ravel()[order]
    transmission = np.asarray(transmittance, dtype=float).ravel()[order]
    index = int(np.argmin(transmission))
    baseline = float(np.percentile(transmission, 90))
    half_level = 0.5 * (baseline + float(transmission[index]))
    below = np.flatnonzero(transmission <= half_level)
    left = below[below < index]
    right = below[below > index]
    if left.size == 0 or right.size == 0:
        raise RuntimeError("resonance FWHM is unresolved; refine spectral sampling")
    width = wavelength[int(right[0])] - wavelength[int(left[-1])]
    if width <= 0:
        raise RuntimeError("invalid resonance linewidth")
    center = float(wavelength[index])
    return center, center / float(width)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    p = parameters(args.mesh_accuracy)
    project = args.output / "resonator.fsp"
    if args.dry_run:
        write_metadata(
            args.output,
            base_metadata(
                template_id=TEMPLATE_ID,
                api_flavor=None,
                completion_state="generated",
                projects=[str(project)],
                parameters=p,
            ),
        )
        return 0

    api, flavor = import_lumerical_api(args.api_path)
    fdtd = api.FDTD(hide=not args.show_gui)
    try:
        build_model(fdtd, p)
        fdtd.save(str(project))
        if args.preview_only:
            state = "generated"
        else:
            fdtd.run()
            result = fdtd.getresult("through_power", "T")
            wavelength = dataset_array(result, "lambda", "wavelength")
            transmittance = np.abs(dataset_array(result, "T"))
            resonance_wavelength, q_factor = loaded_q_from_dip(
                wavelength, transmittance
            )
            np.savez(
                args.output / "resonance.npz",
                wavelength=wavelength,
                frequency=299792458.0 / wavelength,
                transmittance=transmittance,
                resonance_wavelength=resonance_wavelength,
                q_factor=q_factor,
            )
            state = "executed"
        fdtd.save(str(project))
    finally:
        close_session(fdtd)

    metadata = base_metadata(
        template_id=TEMPLATE_ID,
        api_flavor=flavor,
        completion_state=state,
        projects=[str(project)],
        parameters=p,
    )
    metadata["warnings"].append(
        "Loaded Q uses sampled through-port FWHM and requires spectral convergence."
    )
    write_metadata(args.output, metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
