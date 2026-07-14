# Shared FDTD simulation review

Complete this gate before any solver execution.

## Contract and provenance

- [ ] `SimulationContract.v1` passes schema and business validation.
- [ ] Every material choice, polarization, boundary, and accuracy target has
      evidence or an explicitly accepted assumption.
- [ ] Requested observables appear in the raw or derived output contract.
- [ ] Mesh, PML/padding, and run-control convergence cases are proposed.

## Model

- [ ] Physical and solver units are explicit at the adapter boundary.
- [ ] Geometry extents and smallest relevant feature are recorded.
- [ ] Material models cover the full simulation band.
- [ ] Sources and monitors are outside PML.
- [ ] Periodic/Bloch boundaries appear only in physically periodic directions.
- [ ] Symmetry is compatible with geometry, sources, monitors, and fields.
- [ ] Source spectrum covers every monitor frequency.
- [ ] Monitor normals, propagation directions, power signs, and mode bases are
      documented.

## Resources and outputs

- [ ] Memory, runtime, CPU, storage, and license estimates are acceptable.
- [ ] The run directory is isolated and output paths stay inside it.
- [ ] Script/configuration and native model are saved before the expensive run.
- [ ] Raw complex data, axes, units, logs, and metadata have stable names.

## Approval

- [ ] A G2 approval records exactly `base_only` or
      `base_plus_convergence`.
- [ ] Commercial license consumption is explicitly approved.
- [ ] One reduced smoke case will run before sweeps or optimization.
