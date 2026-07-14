# Output and diagnostics

## Reproducible output layout

Keep source, raw data, and derived products distinct:

```text
run/
  model.fsp
  build_model.py
  analysis.lsf
  parameters.json
  environment.json
  raw/
  derived/
  plots/
  validation/
  result-report.md
```

Use relative artifact links in the report. Never overwrite the only copy of an
input project.

## Data formats

- `.fsp`: complete Lumerical project state; not a substitute for source/config.
- NPZ: compact numerical arrays, including complex values.
- JSON: metadata, scalar checks, small real-valued arrays, and warnings.
- CSV: simple tabular real-valued data with one header row; represent complex
  values with explicit real/imaginary columns.
- MAT: use when required by Lumerical/MATLAB interoperability; document dataset
  shape and field names.

For every exported dataset record axis names, units, ordering, normalization,
reference plane, and complex convention. Keep wavelength and frequency axes
when both are used; do not rely on filename units.

## Environment and session failures

1. Confirm the installed Lumerical release and supported Python version.
2. Run `scripts/verify_environment.py` and inspect the resolved module path.
3. Distinguish modern `ansys.lumerical.core` from traditional `lumapi`.
4. Test `--launch-session` only with permission to consume a license.
5. Preserve exact license/interop error text while redacting credentials.
6. Guarantee session closure after exceptions.

Do not diagnose a license failure by changing model settings.

## Model and property failures

- Check SI units and min/max versus centre/span semantics.
- Confirm the expected object exists and has a unique name.
- Avoid dependence on the currently selected object.
- Set prerequisite/override properties before dependent properties.
- Confirm command and property spelling against the installed release.
- Inspect material assignment, mesh order, geometry priority, and imported
  layout scale.

## Empty or implausible monitor data

1. Check source bandwidth, direction, polarization, and amplitude.
2. Check monitor type, orientation, span, and frequency sampling.
3. Inspect available result names and dataset shapes.
4. Verify the source/monitor is not in PML or outside the FDTD region.
5. Check selected guided mode and mode-plane uniformity.
6. Confirm simulation duration and actual termination.
7. Check normalization and power-sign convention.

## Mesh, memory, and runtime failures

- Reduce to a smoke case without changing the physical question.
- Identify local mesh overrides or monitors dominating cell/data count.
- Avoid storing unnecessary field components or excessive frequency points.
- Check thin layers and imported geometry for accidental tiny features.
- Increase resources only after confirming the model is intentional.
- Treat out-of-memory, stalled jobs, and premature auto shutoff as failed runs,
  not zero-valued physics.

## PML, periodicity, and sweep failures

- Move reactive/evanescent fields farther from PML and vary PML layers/type.
- Ensure periodic axes do not also use PML.
- Recheck Bloch phase and broadband-angle assumptions.
- Validate one unswept case before debugging sweep definitions.
- Confirm sweep object/property/result paths and unique output directories.
- Separate license exhaustion from numerical failure.

## Diagnostic order

Use: environment/license → units/material band → object/property state →
source/monitor/mode → mesh/memory/time → boundaries/PML → normalization →
convergence/sweep/output.

Do not alter material loss, geometry, or source physics merely to suppress a
numerical warning.
