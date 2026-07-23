# Human review and automation gates

Automation is unlocked by measured evidence, not a fixed human/agent ratio.

## G1 — Contract

Required before model generation:

- V1 schema validation passes;
- requested observables are present in outputs;
- convergence cases are proposed;
- assumptions that affect physical interpretation are explicitly accepted;
- paper evidence, example suggestions, and agent assumptions remain distinct.
- before simulation code is written, the user selects
  `single_mpi_process` or `multi_mpi_process`;
- the approval records the exact `mpi_processes` value and any required
  launcher/resource configuration;
- the approved process count does not exceed physical cores, memory, licenses,
  or scheduler allocation.

MPI topology is frozen at G1 because it affects generated launch commands,
Lumerical resource setup, MPI-safe I/O, and reproducibility. G2 decides whether
the already-configured code may actually run; it does not silently change MPI
resources.

## G2 — Execution

Required before a smoke or base run:

- geometry/source/monitor/PML/mesh preflight passes;
- estimated memory, runtime, storage, and licenses are acceptable;
- approval records `base_only` or `base_plus_convergence`;
- a Lumerical approval explicitly permits consuming a license seat.

Generating code or requesting a plan is not execution consent.

## G3 — Result and example publication

Required before publishing an `ExampleManifest`:

- solver outputs are readable;
- `ValidationReport` is present;
- every artifact exists and its supplied hash matches;
- license and sensitivity review passes;
- failure-labelled cases are clearly separated from default design priors.
- a legacy/nonconforming source was only read and its before/after tree hash is
  unchanged;
- the published package is self-contained and all internal URIs are relative;
- credentials, required machine-specific paths, path traversal, symlinks, and
  case-insensitive collisions are absent;
- the G3 decision is bound to the exact staged candidate SHA-256;
- the target `example_id@version` does not already exist.

Changing any staged file after review invalidates G3. The case must be
revalidated and reviewed again. Cleaning tools may prepare candidates but may
not write final version directories or catalog entries directly.

An `executed` case may be archived as implementation reference. Only
`validated` or expert-`reviewed` cases are default design baselines.

## G4 — Skill update

Required before merging an ExperienceRecord into a Skill:

- the ExperienceRecord is approved;
- the proposed rule cites source runs/examples;
- the Skill diff is reviewed;
- schema, adapter, and benchmark regression suites pass;
- a rollback target is recorded.

Solver workflows and the Example Library never edit Skills directly.

## Progressive participation metrics

Track per workflow, solver, template, and Skill version:

- schema and preflight pass rate;
- solver execution success rate;
- validation pass rate;
- human rejection and correction rate;
- unresolved failure-type rate;
- benchmark regression rate;
- artifact completeness rate;
- license/session leak count.

Automatic execution or optimization may be enabled only for a scoped capability
after its thresholds are agreed by the project owner. A regression or unknown
failure returns that capability to the preceding gate.
