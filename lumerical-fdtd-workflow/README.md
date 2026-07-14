# Lumerical FDTD Workflow Skill

This project-local, manually invoked Cursor Agent Skill guides reproducible
Ansys Lumerical FDTD simulations.

## Use

Reference the main file in chat:

```text
@lumerical-fdtd-workflow/SKILL.md
```

Then describe the physical problem and requested evidence, for example:

```text
Use this skill to calculate the modal transmission of a silicon waveguide bend
from 1.50 to 1.60 um and propose a mesh-convergence study.
```

The directory intentionally sits outside `.cursor/skills/`, so it is not
automatically discovered. The frontmatter also disables ambient invocation.

## Runtime assumptions

- Ansys Lumerical FDTD and a valid license are installed.
- Python automation is the default:
  `ansys.lumerical.core` is preferred when available, with traditional
  `lumapi` supported for installations that provide it.
- Lumerical Script Language may be used for existing or solver-native flows.
- Python values use SI units unless explicitly converted and labelled.

API names and object properties can vary by release. Confirm them against the
installed documentation and examples.

## Contents

- `SKILL.md`: mandatory workflow and decision rules.
- `checklists/`: requirement, preflight, and reporting gates.
- `references/`: focused Lumerical numerical and API guidance.
- `scripts/verify_environment.py`: import and optional licensed-session check.
- `scripts/validate_results.py`: NPZ/JSON/CSV result checks.
- `templates/`: reviewed parameterized Python starting points for minimal
  waveguide, waveguide-bend R/T, and narrow-band resonator workflows.
- `tool-manifest.yaml` and `solver-capability.yaml`: platform registration and
  capability boundaries.

## Expected workflow

1. Establish the physical and numerical contract.
2. Verify the Python API; explicitly opt in before launching a licensed session.
3. Build and save a parameterized `.fsp` model.
4. Inspect geometry, boundaries, mesh, sources, and monitors.
5. Decide whether convergence validation should be executed.
6. Run a reduced smoke case, then the base case.
7. Optionally run mesh, PML/padding, and run-control convergence cases.
8. Validate the requested observables and save a reproducible report.

The Skill distinguishes **Generated**, **Executed**, and **Validated** work.
Successful execution alone does not establish numerical convergence.
