# Simulation review

Use this gate before the first solver run and repeat it after model changes.

## Runtime

- [ ] `scripts/verify_environment.py` reports a usable API import
- [ ] FDTD session/license launch was tested only with user approval
- [ ] Solver version, Python version, API flavor, and module path are recorded
- [ ] Session closure is guaranteed on success and failure
- [ ] Project/output paths are writable and do not silently overwrite inputs

## Model and units

- [ ] Python geometry, wavelength, and mesh values are in metres
- [ ] Every displayed/exported converted unit is labelled
- [ ] Material models cover the full band and use the intended temperature/data
- [ ] Geometry dimensions and object hierarchy match the specification
- [ ] FDTD region contains propagation padding and all intended structures
- [ ] Global and local mesh choices resolve relevant wavelength/features
- [ ] Estimated memory, storage, and runtime fit available resources

## Sources and boundaries

- [ ] Source type, position, span, direction, and bandwidth are correct
- [ ] Polarization or selected guided mode matches the requested excitation
- [ ] PML occurs only on open boundaries and contains no source/monitor
- [ ] Periodic/Bloch phase is consistent with angle and frequency convention
- [ ] Symmetry boundary parity is compatible with geometry and excitation
- [ ] Evanescent fields have adequate separation from PML

## Monitors and normalization

- [ ] Monitor frequencies lie within the source spectrum
- [ ] Monitor type, orientation, normal, span, and dataset names are explicit
- [ ] Mode-expansion planes lie in uniform waveguide sections
- [ ] Forward/backward and positive/negative power conventions are recorded
- [ ] Reference simulation or source-power normalization is defined if needed
- [ ] Raw complex fields/coefficient data remain available

## Script and project safety

- [ ] Tunable parameters are centralized
- [ ] Object names are unique and stable
- [ ] Order-dependent properties are assigned safely
- [ ] `.fsp` is saved before the expensive run
- [ ] The phase order is parameters → session → model → preview → monitors →
      save → run → validate → export
- [ ] Sweep parameter/result definitions match existing object names

## Smoke test

- [ ] A reduced/coarse case is defined before a production run or sweep
- [ ] Fields and monitor values are finite and nonzero
- [ ] Axes, array shapes, units, and complex conventions were inspected
- [ ] Result magnitude and energy flow are physically plausible
- [ ] No license, mesh, memory, shutoff, or dataset warning is unresolved

## Convergence decision

Immediately before execution, record exactly one:

```text
[ ] Base simulation plus planned convergence validation
[ ] Base simulation only; convergence validation skipped by user choice
Decision by:
Date/time:
```

If convergence is skipped, preserve the proposed cases and do not report a
completion state above **Executed**.
