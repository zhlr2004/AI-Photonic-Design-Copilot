# Monitors and run control

## Observable-first selection

- **Power/transmission monitor**: net spectral power through a plane.
- **Field/profile or DFT monitor**: complex spatial fields versus frequency.
- **Mode-expansion monitor**: forward/backward modal amplitudes and power.
- **Time monitor**: transient decay and resonance/Q analysis.
- **Index monitor**: verify geometry, material assignment, and mesh context.
- **Far-field projection**: angular radiation derived from a suitable
  near-field surface.

Use stable, descriptive monitor names and retrieve results by those names.
Inspect available result/dataset names in the installed release rather than
guessing.

## Frequency sampling

- Ensure all monitor frequencies lie inside the useful source spectrum.
- Specify wavelength/frequency range and number or spacing of sample points.
- Use enough samples to resolve the narrowest expected feature.
- For high-Q resonances, a coarse frequency-domain grid can miss or misestimate
  a peak; combine with adequate time-domain decay analysis where appropriate.
- Record whether interpolation or resampling was applied after retrieval.

## Power and normalization

- Record the monitor normal and sign convention.
- Determine whether a reported transmission is source-normalized, reference-
  normalized, or raw power.
- Use a reference geometry/run when incident power at the measurement plane
  cannot be established reliably in the device simulation.
- Preserve complex mode coefficients before converting to power.
- For multimode ports, include every propagating mode needed for energy balance.
- Do not apply an unexplained absolute value to hide a sign error.

## Run control

- Set a simulation-time ceiling long enough for propagation and decay.
- Use auto shutoff to avoid needless late-time stepping, but verify its
  threshold through convergence cases.
- Save the `.fsp` project before `run`.
- Capture warnings and the actual termination reason when available.
- After running, verify expected monitor results exist before exporting.
- Close the session to release the license.

## Sweeps and jobs

- Run one parameter value successfully before defining a sweep.
- Use stable object/property paths and result names.
- Save sweep definitions and results separately from the base model.
- Distinguish an in-product parameter sweep from Python-managed independent
  sessions.
- Bound parallel jobs by RAM, CPU, and available license features.
- Give every job a unique output directory and deterministic parameter record.
- Resume only after checking which cases completed and whether their model
  version matches.

## Retrieval checks

For every result:

- inspect keys/datasets before indexing;
- record axis names, units, shape, and ordering;
- retain complex values;
- check finite and nonzero data;
- verify wavelength/frequency ordering before comparing cases;
- keep raw arrays separate from derived R/T/S/Q values.

## Workflow-specific notes

- R/T: verify incident normalization and monitor signs; test a simple reference.
- S parameters: place mode-expansion planes in uniform ports and document modal
  phase/reference planes.
- Radiation: confirm the projection surface encloses the source/scatterer and
  excludes PML.
- Resonance/Q: ensure excitation overlaps the mode and the recorded transient is
  long enough to resolve its decay.
