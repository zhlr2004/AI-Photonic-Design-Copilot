# Monitors and run control

## Choose the observable first

| Objective | Primary Meep API |
|---|---|
| transmitted/reflected power | `add_flux`, `get_fluxes` |
| guided-mode amplitudes/S parameters | `add_mode_monitor`, `get_eigenmode_coefficients` |
| complex field at selected frequencies | `add_dft_fields`, `get_dft_array` |
| resonant frequency and Q | `Harminv` |
| radiation pattern | `add_near2far`, `get_farfield(s)` |
| energy spectrum | `add_energy` |
| optical force | `add_force` |
| instantaneous/steady field slice | `get_array` |

Register DFT-based monitors before `run`.

## DFT meaning

Meep accumulates Fourier transforms of the fields during stepping, then forms
quantities such as Poynting flux from those transformed fields. Do not
Fourier-transform an instantaneous time-domain power signal and treat it as
equivalent to Meep's flux spectrum.

## Run forms

```python
sim.run(until=duration)
sim.run(until_after_sources=duration)
sim.run(until_after_sources=mp.stop_when_fields_decayed(...))
sim.run(until_after_sources=mp.stop_when_dft_decayed(...))
```

Use fixed time only when the physical duration is justified, such as a short
visualization or a calibrated Harminv ring-down.

`run` accepts step functions; it is not a Python loop. Use `mp.at_every`,
`mp.after_sources`, `mp.at_beginning`, and related wrappers to control their
execution.

## Stopping conditions

- `stop_when_fields_decayed(T, component, point, decay_by)`: good for localized
  probes when the point is not a field node.
- `stop_when_energy_decayed(T, decay_by)`: useful for a global decay measure.
- `stop_when_dft_decayed(...)`: useful when DFT convergence is the observable.
- `stop_when_flux_decayed(...)`: use for flux-monitor convergence when
  available in the target API version.

Tightening a decay threshold does not fix an undersized domain, poor PML, or
insufficient source bandwidth.

## Reflection/transmission normalization

Use identical discretization and source timing in both runs:

```python
# Reference run
refl = sim.add_flux(...)
tran = sim.add_flux(...)
sim.run(...)
incident_refl_data = sim.get_flux_data(refl)
incident_flux = np.asarray(mp.get_fluxes(tran))

# Device run
refl = sim.add_flux(...)
tran = sim.add_flux(...)
sim.load_minus_flux_data(refl, incident_refl_data)
sim.run(...)

R = -np.asarray(mp.get_fluxes(refl)) / incident_flux
T = np.asarray(mp.get_fluxes(tran)) / incident_flux
```

Subtract incident Fourier fields at the reflection plane. Do not subtract them
at the transmission plane. Keep the reflection plane at the same position
relative to the source in both runs.

## Resonance extraction

Use a broadband pulse to excite candidate modes and run `Harminv` after the
source. Confirm:

- source/probe symmetry overlaps the desired mode;
- extracted modes lie within the requested band;
- frequency and Q remain stable with resolution and ring-down;
- suspicious close/spurious modes are checked with another source/probe.

## Source anchors

- `../../meep-master/python/simulation.py`
- `../../meep-master/src/dft.cpp`
- `../../meep-master/doc/docs/Introduction.md`
- `../../meep-master/doc/docs/The_Run_Function_Is_Not_A_Loop.md`
- `../../meep-master/python/examples/bend-flux.py`
- `../../meep-master/python/examples/ring.py`
- `../../meep-master/python/examples/cavity-farfield.py`
