# Shared FDTD result report

## Identity

```text
workflow_id:
task_id:
run_id:
contract_id and hash:
solver, version, and API flavor:
skill and template version:
```

## Completion state

Select exactly one:

- [ ] `generated`
- [ ] `executed`
- [ ] `validated`

## Objective and model

```text
Objective:
Primary observables:
Geometry and dimensionality:
Materials and valid band:
Source:
Boundaries/PML:
Monitors:
Mesh/discretization:
Run control:
```

## Convergence

```text
User choice: base_only / base_plus_convergence
Performed:
Proposed mesh cases:
Proposed PML/padding cases:
Proposed run-control cases:
Executed cases:
Declared tolerance:
Worst relative difference:
```

If convergence was not performed, the completion state cannot exceed
`executed`.

## Physics checks

- [ ] finite values and valid axes
- [ ] energy/power balance when applicable
- [ ] mode/flux consistency when applicable
- [ ] symmetry, reciprocity, or limiting case when applicable
- [ ] reference or cross-solver comparison when applicable

Record non-applicable checks and the reason.

## Artifacts

```text
Simulation contract:
Script/configuration:
Native model:
Raw data:
Derived data:
Plots:
Environment:
Logs:
RunManifest:
ValidationReport:
```

## Limitations

List unresolved convergence, assumptions, weak incident power, material-fit
limits, dimensional approximations, excluded channels, and solver-specific
constraints.
