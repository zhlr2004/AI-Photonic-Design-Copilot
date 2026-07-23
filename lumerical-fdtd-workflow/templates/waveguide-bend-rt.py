"""Two-run 2D Lumerical FDTD waveguide-bend R/T workflow."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from _common import (
    base_metadata,
    close_session,
    configure_mpi_resources,
    dataset_array,
    import_lumerical_api,
    write_metadata,
)


TEMPLATE_ID = "lumerical-waveguide-bend-rt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/waveguide-bend-rt"))
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
        "core_index": 3.45,
        "x_span_m": 14.0e-6,
        "y_span_m": 14.0e-6,
        "mesh_accuracy": mesh_accuracy,
        "simulation_time_s": 3.0e-12,
        "auto_shutoff_min": 1.0e-5,
    }


def add_region(fdtd: Any, p: dict[str, float | int]) -> None:
    fdtd.addfdtd()
    fdtd.set("name", "fdtd")
    fdtd.set("dimension", "2D")
    fdtd.set("x span", p["x_span_m"])
    fdtd.set("y span", p["y_span_m"])
    fdtd.set("mesh accuracy", p["mesh_accuracy"])
    fdtd.set("simulation time", p["simulation_time_s"])
    fdtd.set("auto shutoff min", p["auto_shutoff_min"])
    for boundary in ("x min bc", "x max bc", "y min bc", "y max bc"):
        fdtd.set(boundary, "PML")


def add_input(fdtd: Any, p: dict[str, float | int]) -> None:
    fdtd.addmode()
    fdtd.set("name", "input_mode")
    fdtd.set("injection axis", "x-axis")
    fdtd.set("direction", "Forward")
    fdtd.set("x", -5.0e-6)
    fdtd.set("y", -2.5e-6)
    fdtd.set("y span", 2.0e-6)
    fdtd.set("wavelength start", p["wavelength_start_m"])
    fdtd.set("wavelength stop", p["wavelength_stop_m"])
    fdtd.set("mode selection", "fundamental mode")

    fdtd.addpower()
    fdtd.set("name", "input_power")
    fdtd.set("monitor type", "2D X-normal")
    fdtd.set("x", -3.5e-6)
    fdtd.set("y", -2.5e-6)
    fdtd.set("y span", 2.0e-6)


def add_reference(fdtd: Any, p: dict[str, float | int]) -> None:
    fdtd.addrect()
    fdtd.set("name", "reference_waveguide")
    fdtd.set("x span", 12.0e-6)
    fdtd.set("y", -2.5e-6)
    fdtd.set("y span", p["waveguide_width_m"])
    fdtd.set("index", p["core_index"])

    fdtd.addpower()
    fdtd.set("name", "output_power")
    fdtd.set("monitor type", "2D X-normal")
    fdtd.set("x", 5.0e-6)
    fdtd.set("y", -2.5e-6)
    fdtd.set("y span", 2.0e-6)


def add_bend(fdtd: Any, p: dict[str, float | int]) -> None:
    fdtd.addrect()
    fdtd.set("name", "input_waveguide")
    fdtd.set("x min", -6.0e-6)
    fdtd.set("x max", 1.0e-6)
    fdtd.set("y", -2.5e-6)
    fdtd.set("y span", p["waveguide_width_m"])
    fdtd.set("index", p["core_index"])

    fdtd.addrect()
    fdtd.set("name", "output_waveguide")
    fdtd.set("x", 1.0e-6)
    fdtd.set("x span", p["waveguide_width_m"])
    fdtd.set("y min", -2.5e-6)
    fdtd.set("y max", 6.0e-6)
    fdtd.set("index", p["core_index"])

    fdtd.addpower()
    fdtd.set("name", "output_power")
    fdtd.set("monitor type", "2D Y-normal")
    fdtd.set("x", 1.0e-6)
    fdtd.set("x span", 2.0e-6)
    fdtd.set("y", 5.0e-6)


def run_case(
    api: Any,
    *,
    p: dict[str, float | int],
    project: Path,
    bend: bool,
    show_gui: bool,
    execute: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    fdtd = api.FDTD(hide=not show_gui)
    try:
        configure_mpi_resources(fdtd, int(p["mpi_processes"]))
        add_region(fdtd, p)
        if bend:
            add_bend(fdtd, p)
        else:
            add_reference(fdtd, p)
        add_input(fdtd, p)
        fdtd.save(str(project))
        if not execute:
            return None
        fdtd.run()
        input_result = fdtd.getresult("input_power", "T")
        output_result = fdtd.getresult("output_power", "T")
        wavelength = dataset_array(output_result, "lambda", "wavelength")
        input_power = np.abs(dataset_array(input_result, "T"))
        output_power = np.abs(dataset_array(output_result, "T"))
        fdtd.save(str(project))
        return wavelength, input_power, output_power
    finally:
        close_session(fdtd)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    p = parameters(args.mesh_accuracy)
    p["mpi_processes"] = args.mpi_processes
    reference_project = args.output / "reference-straight.fsp"
    device_project = args.output / "device-bend.fsp"
    projects = [str(reference_project), str(device_project)]
    if args.dry_run:
        write_metadata(
            args.output,
            base_metadata(
                template_id=TEMPLATE_ID,
                api_flavor=None,
                completion_state="generated",
                projects=projects,
                parameters=p,
            ),
        )
        return 0

    api, flavor = import_lumerical_api(args.api_path)
    if args.preview_only:
        run_case(
            api,
            p=p,
            project=device_project,
            bend=True,
            show_gui=args.show_gui,
            execute=False,
        )
        state = "generated"
    else:
        reference = run_case(
            api,
            p=p,
            project=reference_project,
            bend=False,
            show_gui=args.show_gui,
            execute=True,
        )
        device = run_case(
            api,
            p=p,
            project=device_project,
            bend=True,
            show_gui=args.show_gui,
            execute=True,
        )
        assert reference is not None and device is not None
        wavelength, _, reference_output = reference
        device_wavelength, device_input, device_output = device
        if wavelength.shape != device_wavelength.shape or not np.allclose(
            wavelength, device_wavelength
        ):
            raise RuntimeError("reference and device wavelength axes differ")
        denominator = np.maximum(reference_output, np.finfo(float).tiny)
        transmittance = np.clip(device_output / denominator, 0.0, None)
        reflectance = np.clip(1.0 - device_input, 0.0, None)
        frequency = 299792458.0 / wavelength
        np.savez(
            args.output / "spectra.npz",
            frequency=frequency,
            wavelength=wavelength,
            reflectance=reflectance,
            transmittance=transmittance,
            balance_error=np.abs(1.0 - reflectance - transmittance),
            reference_transmission=reference_output,
        )
        state = "executed"

    write_metadata(
        args.output,
        base_metadata(
            template_id=TEMPLATE_ID,
            api_flavor=flavor,
            completion_state=state,
            projects=projects,
            parameters=p,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
