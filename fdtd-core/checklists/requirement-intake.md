# Shared FDTD requirement intake

Complete this contract before solver selection.

## Objective

- [ ] Physical decision and requested observables are explicit.
- [ ] Dimensionality, coordinate system, and polarization/mode are explicit.
- [ ] Acceptance targets and comparison references are explicit.

## Model

- [ ] Geometry, tolerances, and tunable parameters are listed with units.
- [ ] Every material model has a source and valid spectral range.
- [ ] Sources include spectrum, profile, position, direction, phase, and mode.
- [ ] Boundary intent is specified independently by direction.
- [ ] Monitor type, position, orientation, and canonical output field are listed.

## Numerics and resources

- [ ] Before writing simulation code, the user selected
      `single_mpi_process` or `multi_mpi_process`.
- [ ] `mpi_processes` and, when needed, the MPI launcher are recorded.
- [ ] Multi-process execution does not exceed available physical cores,
      memory, licenses, or scheduler allocation.
- [ ] Mesh/discretization is tied to material wavelength and smallest feature.
- [ ] PML/padding, mesh, and run-control convergence cases are proposed.
- [ ] Runtime, memory, CPU, storage, and license limits are recorded.
- [ ] A reduced smoke case is defined before sweeps or optimization.

## Outputs and validation

- [ ] Raw complex data, axes, units, derived values, and plots are named.
- [ ] Applicable energy, mode, symmetry, reciprocity, resonance, or reference
      checks are selected.
- [ ] Every tolerance has paper, user, or benchmark provenance.

## Assumptions

For each unresolved value:

```text
Parameter ID:
Assumption:
Reason:
Physical consequence:
Accepted by:
```

Do not select a solver or generate a model while a material assumption that
changes physical interpretation remains unaccepted.

Do not write solver code until the MPI execution mode and process count are
accepted at G1.
