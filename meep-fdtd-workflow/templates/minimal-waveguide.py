"""Minimal 2D PyMeep workflow with preview, run, and reproducible output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import meep as mp
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("results/minimal-waveguide"))
    parser.add_argument("--preview-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Physical and numerical parameters: replace deliberately.
    length_unit_um = 1.0
    wavelength_um = 6.67
    fcen = length_unit_um / wavelength_um
    df = 0.2 * fcen
    sx, sy = 16.0, 8.0
    waveguide_width = 1.0
    dpml = 1.0

    cell = mp.Vector3(sx, sy, 0)
    geometry = [
        mp.Block(
            size=mp.Vector3(mp.inf, waveguide_width, mp.inf),
            material=mp.Medium(epsilon=12.0),
        )
    ]
    source_point = mp.Vector3(-0.5 * sx + dpml + 1.0)
    sources = [
        mp.Source(
            mp.GaussianSource(fcen, fwidth=df),
            component=mp.Ez,
            center=source_point,
            size=mp.Vector3(0, waveguide_width),
        )
    ]
    sim = mp.Simulation(
        cell_size=cell,
        geometry=geometry,
        sources=sources,
        boundary_layers=[mp.PML(dpml)],
        resolution=args.resolution,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    sim.plot2D(output_plane=mp.Volume(center=mp.Vector3(), size=cell))
    if mp.am_master():
        import matplotlib.pyplot as plt

        plt.savefig(args.output / "layout.png", dpi=150, bbox_inches="tight")
        plt.close()

    if args.preview_only:
        return

    probe = mp.Vector3(0.5 * sx - dpml - 1.0)
    sim.run(
        until_after_sources=mp.stop_when_fields_decayed(
            50, mp.Ez, probe, 1e-6
        )
    )

    # Meep field access can be collective: execute on all ranks, save on master.
    epsilon = sim.get_array(center=mp.Vector3(), size=cell, component=mp.Dielectric)
    ez = sim.get_array(center=mp.Vector3(), size=cell, component=mp.Ez)

    if mp.am_master():
        np.savez_compressed(args.output / "fields.npz", epsilon=epsilon, ez=ez)
        metadata = {
            "completion_state": "executed",
            "meep_version": mp.__version__,
            "length_unit_um": length_unit_um,
            "wavelength_um": wavelength_um,
            "fcen": fcen,
            "df": df,
            "resolution": args.resolution,
            "dpml": dpml,
        }
        (args.output / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
