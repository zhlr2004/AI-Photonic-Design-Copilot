"""Minimal parameterized 2D Lumerical FDTD waveguide workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from _common import (
    base_metadata,
    close_session,
    configure_mpi_resources,
    dataset_array,
    import_lumerical_api,
    write_metadata,
)


TEMPLATE_ID = "lumerical-minimal-waveguide"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/minimal-waveguide"))
    parser.add_argument("--api-path", type=Path)
    parser.add_argument("--show-gui", action="store_true")
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mesh-accuracy", type=int, default=2)
    parser.add_argument("--mpi-processes", type=int, default=1)
    return parser.parse_args()


def parameters(mesh_accuracy: int) -> dict[str, float | int]:
    return {
        "wavelength_start_m": 1.50e-6,
        "wavelength_stop_m": 1.60e-6,
        "waveguide_width_m": 0.50e-6,
        "waveguide_length_m": 8.0e-6,
        "core_index": 3.45,
        "x_span_m": 10.0e-6,
        "y_span_m": 4.0e-6,
        "mesh_accuracy": mesh_accuracy,
        "simulation_time_s": 2.0e-12,
        "auto_shutoff_min": 1.0e-5,
    }


def build_model(fdtd: object, p: dict[str, float | int]) -> None:
    fdtd.addfdtd()
    fdtd.set("name", "fdtd")
    fdtd.set("dimension", "2D")
    fdtd.set("x span", p["x_span_m"])
    fdtd.set("y span", p["y_span_m"])
    fdtd.set("mesh accuracy", p["mesh_accuracy"])
    fdtd.set("simulation time", p["simulation_time_s"])
    fdtd.set("auto shutoff min", p["auto_shutoff_min"])
    fdtd.set("x min bc", "PML")
    fdtd.set("x max bc", "PML")
    fdtd.set("y min bc", "PML")
    fdtd.set("y max bc", "PML")

    fdtd.addrect()
    fdtd.set("name", "waveguide")
    fdtd.set("x span", p["waveguide_length_m"])
    fdtd.set("y span", p["waveguide_width_m"])
    fdtd.set("index", p["core_index"])

    fdtd.addmode()
    fdtd.set("name", "input_mode")
    fdtd.set("injection axis", "x-axis")
    fdtd.set("direction", "Forward")
    fdtd.set("x", -3.0e-6)
    fdtd.set("y span", 2.0e-6)
    fdtd.set("wavelength start", p["wavelength_start_m"])
    fdtd.set("wavelength stop", p["wavelength_stop_m"])
    fdtd.set("mode selection", "fundamental mode")

    fdtd.addpower()
    fdtd.set("name", "transmission")
    fdtd.set("monitor type", "2D X-normal")
    fdtd.set("x", 3.0e-6)
    fdtd.set("y span", 2.0e-6)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    p = parameters(args.mesh_accuracy)
    p["mpi_processes"] = args.mpi_processes
    project = args.output / "minimal-waveguide.fsp"
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
        configure_mpi_resources(fdtd, args.mpi_processes)
        build_model(fdtd, p)
        fdtd.save(str(project))
        if args.preview_only:
            state = "generated"
        else:
            fdtd.run()
            result = fdtd.getresult("transmission", "T")
            wavelength = dataset_array(result, "lambda", "wavelength")
            transmittance = np.abs(dataset_array(result, "T"))
            frequency = 299792458.0 / wavelength
            np.savez(
                args.output / "spectra.npz",
                frequency=frequency,
                wavelength=wavelength,
                transmittance=transmittance,
            )
            state = "executed"
        fdtd.save(str(project))
    finally:
        close_session(fdtd)

    write_metadata(
        args.output,
        base_metadata(
            template_id=TEMPLATE_ID,
            api_flavor=flavor,
            completion_state=state,
            projects=[str(project)],
            parameters=p,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
