"""Broadband reflection/transmission using Meep's two-run normalization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import meep as mp
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", type=int, default=20)
    parser.add_argument("--dpml", type=float, default=1.0)
    parser.add_argument("--decay-by", type=float, default=1e-6)
    parser.add_argument("--output", type=Path, default=Path("results/flux-two-run"))
    return parser.parse_args()


def build_simulation(
    geometry: list,
    sources: list,
    cell: mp.Vector3,
    dpml: float,
    resolution: int,
) -> mp.Simulation:
    return mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(dpml)],
        geometry=geometry,
        sources=sources,
        resolution=resolution,
    )


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    sx, sy = 16.0, 32.0
    pad, width = 4.0, 1.0
    cell = mp.Vector3(sx, sy)
    x_center = 0.5 * (sx - width - 2 * pad)
    y_center = -0.5 * (sy - width - 2 * pad)

    fcen, df, nfreq = 0.15, 0.1, 100
    sources = [
        mp.Source(
            mp.GaussianSource(fcen, fwidth=df),
            component=mp.Ez,
            center=mp.Vector3(-0.5 * sx + args.dpml, y_center),
            size=mp.Vector3(0, width),
        )
    ]

    reflection_region = mp.FluxRegion(
        center=mp.Vector3(-0.5 * sx + args.dpml + 0.5, y_center),
        size=mp.Vector3(0, 2 * width),
    )

    # Run 1: straight reference waveguide. Keep all shared settings unchanged.
    reference_geometry = [
        mp.Block(
            size=mp.Vector3(mp.inf, width, mp.inf),
            center=mp.Vector3(0, y_center),
            material=mp.Medium(epsilon=12.0),
        )
    ]
    sim = build_simulation(
        reference_geometry, sources, cell, args.dpml, args.resolution
    )
    reflection = sim.add_flux(fcen, df, nfreq, reflection_region)
    reference_transmission_region = mp.FluxRegion(
        center=mp.Vector3(0.5 * sx - args.dpml, y_center),
        size=mp.Vector3(0, 2 * width),
    )
    transmission = sim.add_flux(fcen, df, nfreq, reference_transmission_region)
    reference_probe = mp.Vector3(0.5 * sx - args.dpml - 0.5, y_center)
    sim.run(
        until_after_sources=mp.stop_when_fields_decayed(
            50, mp.Ez, reference_probe, args.decay_by
        )
    )
    incident_reflection_data = sim.get_flux_data(reflection)
    incident_flux = np.asarray(mp.get_fluxes(transmission), dtype=float)

    # Run 2: device. Reflection fields are incident-subtracted before stepping.
    device_geometry = [
        mp.Block(
            size=mp.Vector3(sx - pad, width, mp.inf),
            center=mp.Vector3(-0.5 * pad, y_center),
            material=mp.Medium(epsilon=12.0),
        ),
        mp.Block(
            size=mp.Vector3(width, sy - pad, mp.inf),
            center=mp.Vector3(x_center, 0.5 * pad),
            material=mp.Medium(epsilon=12.0),
        ),
    ]
    sim = build_simulation(device_geometry, sources, cell, args.dpml, args.resolution)
    reflection = sim.add_flux(fcen, df, nfreq, reflection_region)
    device_transmission_region = mp.FluxRegion(
        center=mp.Vector3(x_center, 0.5 * sy - args.dpml - 0.5),
        size=mp.Vector3(2 * width, 0),
    )
    transmission = sim.add_flux(fcen, df, nfreq, device_transmission_region)
    sim.load_minus_flux_data(reflection, incident_reflection_data)
    device_probe = mp.Vector3(x_center, 0.5 * sy - args.dpml - 0.5)
    sim.run(
        until_after_sources=mp.stop_when_fields_decayed(
            50, mp.Ez, device_probe, args.decay_by
        )
    )

    frequencies = np.asarray(mp.get_flux_freqs(reflection), dtype=float)
    reflected_flux = np.asarray(mp.get_fluxes(reflection), dtype=float)
    transmitted_flux = np.asarray(mp.get_fluxes(transmission), dtype=float)
    if np.any(np.isclose(incident_flux, 0.0)):
        raise RuntimeError("incident flux contains zero; normalization is invalid")

    reflectance = -reflected_flux / incident_flux
    transmittance = transmitted_flux / incident_flux
    balance_error = 1.0 - reflectance - transmittance

    if mp.am_master():
        np.savez_compressed(
            args.output / "spectra.npz",
            frequency=frequencies,
            wavelength=1.0 / frequencies,
            incident_flux=incident_flux,
            reflected_flux=reflected_flux,
            transmitted_flux=transmitted_flux,
            reflectance=reflectance,
            transmittance=transmittance,
            balance_error=balance_error,
        )
        metadata = {
            "completion_state": "executed",
            "meep_version": mp.__version__,
            "resolution": args.resolution,
            "dpml": args.dpml,
            "decay_by": args.decay_by,
            "note": "Run convergence cases before changing state to validated.",
        }
        (args.output / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
