# Human review and automation gates

Automation is unlocked by measured evidence, not a fixed human/agent ratio.

## G1 — Contract

Required before model generation:

- V1 schema validation passes;
- requested observables are present in outputs;
- convergence cases are proposed;
- assumptions that affect physical interpretation are explicitly accepted;
- paper evidence, example suggestions, and agent assumptions remain distinct.

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
