"""MPI subgroup parameter sweep based on Meep's regression-test pattern."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import meep as mp
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=2)
    parser.add_argument("--resolution", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("results/mpi-sweep"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if mp.count_processors() < args.cases:
        raise RuntimeError("MPI process count must be at least the number of cases")
    if mp.count_processors() % args.cases != 0:
        raise RuntimeError("MPI process count must be divisible by case count")

    # Every rank executes this branch; Meep creates independent subcommunicators.
    case_index = mp.divide_parallel_processes(args.cases)
    frequencies = np.linspace(0.4, 1.0, args.cases)
    fcen = float(frequencies[case_index])

    interior, dpml = 4.0, 1.0
    cell = mp.Vector3(interior + 2 * dpml, interior + 2 * dpml)
    sim = mp.Simulation(
        cell_size=cell,
        resolution=args.resolution,
        boundary_layers=[mp.PML(dpml)],
        sources=[
            mp.Source(
                mp.GaussianSource(fcen, fwidth=0.2 * fcen),
                component=mp.Ez,
                center=mp.Vector3(),
            )
        ],
        symmetries=[mp.Mirror(mp.X), mp.Mirror(mp.Y)],
    )
    half = 0.5 * interior
    flux_box = sim.add_flux(
        fcen,
        0,
        1,
        mp.FluxRegion(mp.Vector3(y=half), size=mp.Vector3(interior)),
        mp.FluxRegion(
            mp.Vector3(y=-half), size=mp.Vector3(interior), weight=-1
        ),
        mp.FluxRegion(mp.Vector3(half), size=mp.Vector3(y=interior)),
        mp.FluxRegion(
            mp.Vector3(-half), size=mp.Vector3(y=interior), weight=-1
        ),
        decimation_factor=1,
    )
    sim.run(until_after_sources=30)
    total_flux = float(mp.get_fluxes(flux_box)[0])

    merged_case = np.asarray(mp.merge_subgroup_data(case_index))
    merged_frequency = np.asarray(mp.merge_subgroup_data(fcen))
    merged_flux = np.asarray(mp.merge_subgroup_data(total_flux))

    # am_master() is true once per subgroup; only the overall master writes.
    if mp.am_really_master():
        args.output.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            args.output / "sweep.npz",
            case=merged_case,
            frequency=merged_frequency,
            total_flux=merged_flux,
        )
        metadata = {
            "completion_state": "executed",
            "meep_version": mp.__version__,
            "mpi_processes": mp.count_processors(),
            "cases": args.cases,
            "resolution": args.resolution,
            "launch": "mpirun -np N python -m mpi4py mpi-parameter-sweep.py",
        }
        (args.output / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
