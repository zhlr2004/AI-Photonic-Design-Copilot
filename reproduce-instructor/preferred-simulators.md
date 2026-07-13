# Preferred Simulators and Simulation Libraries

Use this file as a preference list, not an absolute restriction. Select a tool
only when its numerical method matches the paper, it can be automated, and it
can export traceable solver results. A technically better tool outside this
list is allowed when the generated `instruction.md` explains why.

Do not choose software merely because it appears here. Verify that the required
API/library, solver capability, installation, and license are available before
committing the reproduction task to it.

## Selection Priority

Apply these rules in order:

1. Prefer the solver and numerical method reported by the paper when they can be
   automated and reproduce the requested observable.
2. Otherwise choose a method appropriate to the target physics, geometry,
   dimensionality, bandwidth, periodicity, material model, and accuracy.
3. Prefer a maintained API/library or stable scripting/batch interface over a
   GUI-only workflow.
4. If multiple tools satisfy the task, perform non-destructive availability
   checks before selecting one: verify package/API discovery, version, and
   license or service access where safely queryable.
5. Prefer tools that save a complete model/configuration and native raw results.
6. Consider license access, hardware, runtime, memory, and reproducibility before
   selecting a commercial or cloud service.
7. Do not replace a required full-wave or multiphysics calculation with a
   lower-fidelity model unless the paper and target observable justify it.

## Preferred Tools

- **Ansys Lumerical FDTD** — Commercial FDTD software for modeling and solving
  photonic and electromagnetic structures through an automation (lumapi).
- **Meep** — Open-source FDTD library with Python and Scheme interfaces for
  electromagnetic field, spectrum, and near-/far-field simulations.

## Method-to-Task Guide

| Task characteristic | Preferred method |
| --- | --- |
| Broadband pulse response, transient dynamics, or near/far fields | FDTD |
| High-index-contrast resonator, irregular 3D geometry, or coupled physics | FEM |
| Periodic layered metasurface or diffraction-order spectrum | RCWA |
| Open-region scattering represented efficiently by surfaces | BEM |
| Band structure, eigenfrequency, or mode profile | Eigenmode solver |
| Validated component network or system-level photonic circuit | Circuit/S-parameter solver |
| Optical response coupled to heat, mechanics, charge, or transport | Multiphysics FEM or an explicitly coupled solver workflow |

Use this guide only as a starting point. The paper's governing equations,
reported method, and target observable determine the final choice.

## Admission Criteria for Other Tools

A tool not listed above may be used only if the generated instruction documents:

- the numerical method and why it fits the paper;
- a maintained library, official API, scripting interface, or reliable batch
  interface used to construct and solve the model;
- how geometry, materials, sources, boundaries, discretization, and
  monitors/probes are created programmatically;
- how model/configuration, run metadata, raw results, CSV, and PNG are saved;
- how convergence and physical validity will be tested;
- any license, service, hardware, or reproducibility limitations.

Reject GUI-only tools, inaccessible APIs, abandoned dependencies without a
reproducible environment, and tools that cannot expose solver-derived data
needed for traceability.
