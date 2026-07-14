"""Advanced templates: dipole near-to-far or guided-mode decomposition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import meep as mp
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", choices=("near2far", "mode"))
    parser.add_argument("--resolution", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("results/near2far-mode"))
    return parser.parse_args()


def run_near2far(resolution: int) -> dict[str, np.ndarray]:
    fcen = 0.5
    dpml, interior = 1.0, 6.0
    cell = mp.Vector3(interior + 2 * dpml, interior + 2 * dpml)
    sim = mp.Simulation(
        cell_size=cell,
        resolution=resolution,
        boundary_layers=[mp.PML(dpml)],
        sources=[
            mp.Source(
                mp.GaussianSource(fcen, fwidth=0.2 * fcen),
                component=mp.Ez,
                center=mp.Vector3(),
            )
        ],
    )

    half = 0.5 * interior
    n2f = sim.add_near2far(
        fcen,
        0,
        1,
        mp.Near2FarRegion(mp.Vector3(y=half), size=mp.Vector3(interior, 0)),
        mp.Near2FarRegion(
            mp.Vector3(y=-half),
            size=mp.Vector3(interior, 0),
            weight=-1,
        ),
        mp.Near2FarRegion(mp.Vector3(half), size=mp.Vector3(0, interior)),
        mp.Near2FarRegion(
            mp.Vector3(-half),
            size=mp.Vector3(0, interior),
            weight=-1,
        ),
    )
    sim.run(until_after_sources=mp.stop_when_dft_decayed())

    angles = np.linspace(0.0, 2.0 * np.pi, 361)
    radius = 100.0
    fields = np.asarray(
        [
            sim.get_farfield(
                n2f, mp.Vector3(radius * np.cos(theta), radius * np.sin(theta))
            )
            for theta in angles
        ],
        dtype=complex,
    )
    return {"angle_rad": angles, "far_fields": fields}


def run_mode(resolution: int) -> dict[str, np.ndarray]:
    fcen = 0.15
    dpml_x, dpml_y = 2.0, 1.0
    sx, sy, width = 14.0, 7.0, 1.0
    cell = mp.Vector3(sx, sy)
    parity = mp.ODD_Z + mp.EVEN_Y
    source_x = -0.5 * sx + dpml_x + 1.0
    monitor_x = 0.5 * sx - dpml_x - 1.0

    sim = mp.Simulation(
        cell_size=cell,
        resolution=resolution,
        boundary_layers=[
            mp.PML(dpml_x, direction=mp.X),
            mp.PML(dpml_y, direction=mp.Y),
        ],
        geometry=[
            mp.Block(
                size=mp.Vector3(mp.inf, width, mp.inf),
                material=mp.Medium(epsilon=12.0),
            )
        ],
        sources=[
            mp.EigenModeSource(
                src=mp.GaussianSource(fcen, fwidth=0.2 * fcen),
                center=mp.Vector3(source_x),
                size=mp.Vector3(0, sy - 2 * dpml_y),
                eig_match_freq=True,
                eig_parity=parity,
            )
        ],
        symmetries=[mp.Mirror(mp.Y)],
    )
    monitor_point = mp.Vector3(monitor_x)
    flux = sim.add_flux(
        fcen,
        0,
        1,
        mp.FluxRegion(
            center=monitor_point,
            size=mp.Vector3(0, sy - 2 * dpml_y),
        ),
    )
    sim.run(
        until_after_sources=mp.stop_when_fields_decayed(
            50, mp.Ez, monitor_point, 1e-7
        )
    )
    coefficients = sim.get_eigenmode_coefficients(flux, [1], eig_parity=parity)
    return {
        "frequency": np.asarray(mp.get_flux_freqs(flux), dtype=float),
        "flux": np.asarray(mp.get_fluxes(flux), dtype=float),
        "alpha": np.asarray(coefficients.alpha, dtype=complex),
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = (
        run_near2far(args.resolution)
        if args.workflow == "near2far"
        else run_mode(args.resolution)
    )

    if mp.am_master():
        np.savez_compressed(args.output / f"{args.workflow}.npz", **results)
        metadata = {
            "completion_state": "executed",
            "workflow": args.workflow,
            "resolution": args.resolution,
            "meep_version": mp.__version__,
            "note": "Validate against direct DFT/analytic fields or flux power.",
        }
        (args.output / f"{args.workflow}.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
