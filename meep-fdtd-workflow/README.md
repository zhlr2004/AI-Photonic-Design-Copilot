# Meep FDTD Workflow Skill

This directory contains a project-local, manually invoked Cursor Agent Skill
for end-to-end PyMeep simulations.

## Use

Reference the main file in chat:

```text
@meep-fdtd-workflow/SKILL.md
```

Then describe the physical problem, for example:

```text
Use this skill to calculate the reflection and transmission spectrum of a
silicon waveguide bend from 1.50 to 1.60 um and verify convergence.
```

This directory is intentionally outside `.cursor/skills/`; Cursor will not
automatically discover it. The frontmatter also disables ambient model
invocation.

## Runtime assumption

- Linux or WSL2
- Conda environment from `conda-forge`
- PyMeep Python API
- Optional MPICH build for MPI runs

The installed PyMeep version and matching official documentation are the
default API reference. A local Meep source checkout is optional and must have
its revision recorded when used for implementation-level diagnosis.

## Contents

- `SKILL.md`: the mandatory workflow and decision rules.
- `references/`: focused Meep numerical and API guidance.
- `templates/`: parameterized starting points based on official examples/tests.
- `checklists/`: requirement, preflight, and reporting gates.
- `scripts/verify_environment.py`: runtime smoke test.
- `scripts/validate_results.py`: generic NPZ/JSON result checks.
- `tool-manifest.yaml` and `solver-capability.yaml`: platform registration and
  capability boundaries.

## Expected workflow

1. Gather the physical and numerical contract.
2. Verify PyMeep in WSL/Linux.
3. Generate or adapt a template.
4. Preview the simulation layout.
5. Before running Meep, ask whether convergence validation should be executed.
6. Execute a coarse/base case.
7. Optionally run the convergence cases; their proposed configuration remains
   in the plan even when skipped.
8. Validate the requested physics checks and save a report.

The Skill distinguishes generated, executed, and validated work. A successful
Meep process alone is not evidence of numerical convergence. If convergence is
skipped, the highest completion state is `Executed`.
