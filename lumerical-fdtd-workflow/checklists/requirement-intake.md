# Requirement intake

Complete this contract before building the model. Ask only about omissions that
materially affect physics, cost, or interpretation.

## Physical objective

- [ ] Device/problem and decision the simulation must support
- [ ] Requested observables: fields, R/T/A, S parameters, mode overlap, Q,
      radiation pattern, force, or another quantity
- [ ] Required dimensionality: 2D, 2.5D approximation, or 3D
- [ ] Coordinate system and reference planes
- [ ] Acceptance threshold and intended comparison/reference

## Geometry and materials

- [ ] Geometry dimensions, tolerances, and parameterized variables
- [ ] Background/cladding/substrate and finite layer extents
- [ ] Material source: Lumerical database, measured data, or fitted model
- [ ] Temperature, anisotropy, nonlinear response, gain, or loss assumptions
- [ ] Material-data validity across the full wavelength/frequency band
- [ ] Smallest feature and any interfaces needing a local mesh override

Do not replace a missing dispersive model with an arbitrary constant index.

## Excitation and spectrum

- [ ] Wavelength or frequency range and sampling requirement
- [ ] Source type: plane wave, Gaussian, mode, dipole, TFSF, or imported field
- [ ] Injection axis/direction and source position/span
- [ ] Polarization basis or guided-mode order and mode-selection rule
- [ ] Coherence, phase, amplitude, and normalization convention

## Boundaries and monitors

- [ ] Open directions and PML type/layers
- [ ] Periodic/Bloch directions and phase/wave-vector convention
- [ ] Symmetric/antisymmetric or metallic boundaries and field parity
- [ ] Monitor types, locations, orientations, and names
- [ ] Port reference planes and forward/backward power convention
- [ ] Near-field/far-field surface and angular sampling, if applicable

## Accuracy and resources

- [ ] Target error for each primary observable
- [ ] Global mesh accuracy and planned local mesh spacing
- [ ] PML/padding and run-control convergence cases
- [ ] Simulation-time ceiling and auto-shutoff threshold
- [ ] Available RAM, CPU cores, storage, licenses, and runtime budget
- [ ] Parameter-sweep or optimization dimensions and stopping criteria

## Output contract

- [ ] `.fsp` project and Python/LSF source
- [ ] Raw complex datasets with axes and units
- [ ] Derived quantities and plots
- [ ] Parameter, environment, version, and completion-state metadata
- [ ] File naming and output directory

## Assumption record

For every unresolved material choice, record:

```text
Assumption:
Reason:
Consequence:
Accepted by:
```

Do not proceed past model design with an unaccepted assumption that changes the
requested physical interpretation.
