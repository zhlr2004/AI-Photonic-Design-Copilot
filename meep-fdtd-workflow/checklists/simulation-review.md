# Simulation preflight review

Do not start an expensive run until this review passes.

## Environment

- [ ] Running under Linux/WSL in the intended Conda environment.
- [ ] `verify_environment.py` passes.
- [ ] Meep version and serial/MPI build recorded.

## Units, materials, and grid

- [ ] One length unit is used consistently.
- [ ] Frequency conversion is `f = 1 / lambda_vacuum`.
- [ ] Material fits are valid across the full band.
- [ ] Shortest material wavelength and smallest feature are calculated.
- [ ] Resolution is justified by both wavelength and geometry.
- [ ] Courant factor satisfies refractive-index and material-pole constraints.
- [ ] Estimated grid size, memory, and runtime fit the resource budget.

## Geometry and boundaries

- [ ] Geometry order/overlap gives the intended material precedence.
- [ ] Layout plot shows cell, geometry, PML, source, and monitors.
- [ ] PML is inside the cell and only in open directions.
- [ ] Source, monitors, and physical outputs are outside PML.
- [ ] Padding prevents relevant evanescent fields from reaching PML.
- [ ] Periodicity and Bloch vector match the unit cell.
- [ ] Symmetry parity is consistent with geometry, source, and desired mode.

## Source and monitors

- [ ] Source spectrum covers all monitor frequencies with usable amplitude.
- [ ] Source field component matches the intended polarization.
- [ ] Reflection monitor lies between source and scatterer.
- [ ] Transmission/mode monitor lies in a uniform output region.
- [ ] Decay probe is not at a symmetry or modal node.
- [ ] near2far regions form the required closed surface with correct weights.

## Workflow correctness

- [ ] DFT monitors are created before `run`.
- [ ] Stop condition is tied to the requested observable.
- [ ] R/T reference and device runs use identical discretization and source.
- [ ] Incident subtraction is applied only to reflected fields.
- [ ] MPI collectives run on all ranks; only external I/O is master-guarded.

## Smoke test

- [ ] Convergence protocol is included in the plan.
- [ ] Before any Meep execution, user chose either base-only execution or base
      plus convergence validation.
- [ ] User choice is recorded in metadata/report.
- [ ] Coarse case completes without warnings or NaN/Inf.
- [ ] Fields/flux are nonzero in the useful band.
- [ ] Output files reopen successfully.
- [ ] One representative plot has physically plausible geometry and fields.
- [ ] Proposed production convergence cases remain listed even when skipped.
