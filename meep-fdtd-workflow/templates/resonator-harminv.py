"""Ring-resonator frequency/Q extraction with Harminv."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import meep as mp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", type=int, default=20)
    parser.add_argument("--dpml", type=float, default=2.0)
    parser.add_argument("--ring-down", type=float, default=300.0)
    parser.add_argument(
        "--output", type=Path, default=Path("results/resonator-harminv")
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    refractive_index = 3.4
    ring_width = 1.0
    inner_radius = 1.0
    padding = 4.0
    cell_width = 2 * (inner_radius + ring_width + padding + args.dpml)
    fcen, df = 0.15, 0.1
    probe = mp.Vector3(inner_radius + 0.1)

    geometry = [
        mp.Cylinder(
            radius=inner_radius + ring_width,
            material=mp.Medium(index=refractive_index),
        ),
        mp.Cylinder(radius=inner_radius),
    ]
    sources = [
        mp.Source(
            mp.GaussianSource(fcen, fwidth=df),
            component=mp.Ez,
            center=probe,
        )
    ]
    sim = mp.Simulation(
        cell_size=mp.Vector3(cell_width, cell_width),
        geometry=geometry,
        sources=sources,
        resolution=args.resolution,
        symmetries=[mp.Mirror(mp.Y)],
        boundary_layers=[mp.PML(args.dpml)],
    )

    harminv = mp.Harminv(mp.Ez, probe, fcen, df)
    sim.run(mp.after_sources(harminv), until_after_sources=args.ring_down)

    modes = [
        {
            "frequency": mode.freq,
            "decay": mode.decay,
            "quality_factor": mode.Q,
            "amplitude_real": mode.amp.real,
            "amplitude_imag": mode.amp.imag,
            "error": mode.err,
        }
        for mode in harminv.modes
    ]
    metadata = {
        "completion_state": "executed",
        "meep_version": mp.__version__,
        "resolution": args.resolution,
        "dpml": args.dpml,
        "ring_down": args.ring_down,
        "fcen": fcen,
        "df": df,
        "modes": modes,
        "validation_required": [
            "increase resolution",
            "increase PML/padding",
            "increase ring-down",
            "repeat with another source/probe",
        ],
    }
    if mp.am_master():
        (args.output / "modes.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
