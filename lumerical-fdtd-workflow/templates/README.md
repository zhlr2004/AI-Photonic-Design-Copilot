# Reviewed starting templates

The directory contains:

- `minimal-waveguide.py`: minimal 2D field/transmission workflow;
- `waveguide-bend-rt.py`: reference/device broadband bend workflow;
- `resonator-narrowband.py`: ring spectrum and sampled loaded-Q estimate;
- `_common.py`: API import, dataset, metadata, and session helpers.

Each template supports `--dry-run` without importing Lumerical. `--preview-only`
still opens an FDTD session and therefore requires explicit license approval.

Before adding or changing a template:

- verify it against the supported Lumerical release;
- centralize physical and numerical parameters;
- preserve the workflow order documented in `../SKILL.md`;
- document units, object names, normalization, outputs, and completion state;
- include a preflight view and convergence plan;
- avoid embedding credentials, machine-specific paths, or license settings.

Do not treat a template as validated merely because it runs. The current
templates emit `executed` after a solver run; convergence must be performed
separately before the platform can promote a run to `validated`.
