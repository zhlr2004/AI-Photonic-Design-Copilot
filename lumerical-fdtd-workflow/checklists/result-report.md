# Result report

Use this structure for the final handoff.

## Completion state

State exactly one:

- **Generated**: scripts/project logic created; FDTD not run.
- **Executed**: outputs produced; convergence not established.
- **Validated**: declared convergence and physics checks passed.

## Objective and outcome

- Physical question:
- Primary observable:
- Main result:
- Acceptance threshold:
- Outcome against threshold:

## Environment

- Platform:
- Python version/executable:
- API flavor and module path:
- Lumerical FDTD version:
- License/execution mode:
- Launch command:

## Model

- Project (`.fsp`):
- Python/LSF source:
- Dimensionality and units:
- Geometry/configuration snapshot:
- Materials and data sources:
- Source and polarization/mode:
- Boundaries and symmetry:
- Monitor/reference-plane definitions:

## Numerical configuration

- Wavelength/frequency sampling:
- Global mesh accuracy:
- Local mesh overrides:
- PML type/layers and padding:
- Simulation-time ceiling:
- Auto-shutoff threshold:
- Estimated/observed memory and runtime:

## Validation

- User convergence choice:
- Proposed convergence cases:
- Executed convergence cases:
- Primary-observable differences:
- Energy/reciprocity/modal/symmetry checks:
- `validate_results.py` report:

If validation was skipped, write `not performed by user choice`.

## Artifacts

- Raw complex datasets:
- Frequency/wavelength axes:
- Derived data:
- Plots:
- Sweep/optimization definitions and results:
- Metadata and logs:

## Assumptions, warnings, and limitations

- Accepted assumptions:
- Solver/API warnings:
- Known model limitations:
- Unresolved risks:
- Recommended next action:

Never describe a result as converged, validated, or physically trustworthy
without citing the corresponding evidence and tolerance.
