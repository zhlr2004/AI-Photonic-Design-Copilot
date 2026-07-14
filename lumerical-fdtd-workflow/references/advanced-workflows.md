# Advanced workflows

Use these branches only after a reduced forward model passes preflight.

## Modal S parameters

- Use mode sources/ports and mode-expansion monitors in uniform waveguide
  sections.
- Record mode selection, propagation direction, phase, and reference plane.
- Include all relevant propagating modes and verify modal power against total
  monitor power.
- De-embed or shift reference planes only with a documented phase convention.
- Test reciprocity only after consistent port normalization.

## Periodic and diffractive structures

- Model one unit cell with periodic/Bloch boundaries on periodic axes.
- Apply PML only along open axes.
- Keep incidence angle, Bloch phase, lattice vector, and frequency conventions
  consistent.
- Sum every propagating reflected/transmitted diffraction order for energy
  balance.
- Check enough spatial and spectral sampling to resolve high orders.

## Far-field projection

- Use a documented monitor surface that encloses the radiator/scatterer and
  stays outside sources and PML.
- Ensure sampled near fields satisfy the projection assumptions.
- Select enough angular points for lobes and integrated power.
- Record polarization and coordinate conventions.
- Compare projected integrated power with a suitable power monitor in a reduced
  case.

## Resonance and Q

- Use a broadband pulse or appropriate narrow-band excitation with spatial and
  polarization overlap to the expected mode.
- Record a sufficiently long transient after excitation.
- Separate radiative, absorptive, and coupling loss when the interpretation
  requires it.
- Repeat with another source/probe location to detect missed modes.
- Validate frequency and Q against mesh, PML/padding, and record duration.

## Parameter sweeps

- Validate one base parameter value first.
- Keep geometry parameters separate from numerical convergence parameters.
- Save the sweep definition, parameter list, failed cases, and result names.
- Use deterministic job directories and avoid sharing writable project files.
- Check RAM and license capacity before parallel execution.
- Re-evaluate the selected optimum with tighter numerical settings.

## Optimization and LumOpt

Optimization is not a substitute for a validated forward model.

1. Validate fixed geometry, source, monitors, ports, and objective.
2. Define bounded design variables and manufacturability constraints.
3. Record material interpolation, filtering, projection, and initialization.
4. Verify one gradient/directional derivative with finite differences when an
   adjoint workflow is used.
5. Save checkpoints and objective history deterministically.
6. Rebuild and validate the final design at tighter mesh/PML/run settings.
7. Test robustness to fabrication-relevant perturbations.

Confirm LumOpt compatibility with the installed Python and Lumerical release;
do not mix examples from incompatible releases without checking APIs.

## LSF interoperability

- Keep reusable solver-native functions in reviewed `.lsf` files.
- Call them from Python through documented script loading/evaluation.
- Pass data with supported API transfer methods and record array orientation.
- Avoid constructing long LSF programs from unescaped user strings.
- Store the exact LSF alongside the Python driver and `.fsp` project.

## Remote and cluster execution

- Distinguish remote API/interop sessions from local batch jobs and product
  resource-manager jobs.
- Record host-independent paths or explicit staging rules.
- Do not expose license-server credentials in logs or metadata.
- Validate one local/reduced case before distributing a sweep.
- Give each job isolated writable output and capture exit status/warnings.
- Treat missing output caused by scheduling/license failure separately from
  numerical nonconvergence.
