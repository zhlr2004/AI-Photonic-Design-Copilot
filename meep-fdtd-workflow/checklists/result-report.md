# Result report

Use this structure for every completed workflow.

## Completion state

Select one:

- [ ] Generated: code only; Meep was not executed.
- [ ] Executed: outputs exist; convergence is not established.
- [ ] Validated: all declared numerical and physical checks pass.

## Objective and conclusion

```text
Objective:
Primary observable:
Result:
Physical interpretation:
```

## Environment

```text
OS/WSL:
Python:
Meep:
MPI and process count:
Conda environment:
Command:
Source revision/template:
```

## Model

```text
Length unit:
Dimensions/coordinates:
Cell:
Geometry:
Materials and valid band:
Source:
Boundaries/PML:
Symmetry/k-point:
Monitors:
```

## Numerical parameters

```text
Resolution:
Courant:
PML/absorber thickness:
Stop condition:
DFT frequencies:
Grid/chunk estimate:
```

## Convergence evidence

Record the user's pre-execution choice. If validation was selected, record each
independent change and relative difference. If it was skipped, retain the
proposed cases and mark them as not performed.

```text
User choice: base only / base plus convergence validation
Convergence status: performed / not performed by user choice
Resolution cases:
PML/padding cases:
Decay/run-duration cases:
Declared tolerance:
Worst relative change:
Pass/fail:
```

Convergence status `not performed` limits the overall completion state to
`Executed`.

## Physics checks

- [ ] Energy/power balance.
- [ ] Analytic or known-reference comparison.
- [ ] Flux versus mode coefficient, or near2far versus DFT.
- [ ] Symmetry-on versus symmetry-off reduced case.
- [ ] Material model verified over the band.

Record non-applicable items and why.

## Artifacts

```text
Simulation script:
Raw data:
Derived data:
Plots:
Metadata:
Logs:
Validation output:
```

## Limitations and warnings

List dimensional approximations, excluded channels, frequencies with weak
incident power, unresolved convergence, material-fit limits, and known PML or
MPI constraints.
