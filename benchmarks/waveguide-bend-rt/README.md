# Waveguide-bend R/T dual-solver benchmark

`simulation-contract.json` is the common input for `MeepSolverAdapter` and
`LumericalSolverAdapter`.

The benchmark verifies:

- both adapters accept the same contract and retain the same canonical hash;
- each output contains wavelength/frequency, reflectance, and transmittance;
- each solver independently passes finite-axis and R/T balance checks;
- mesh, PML, and run-control cases are independently varied when approved;
- spectral trend correlation is checked after interpolation to a common axis;
- scripts, native models, raw data, metadata, and validation reports are
  traceable.

Pointwise equality is not required because discretization, source
normalization, PML implementation, and material representation differ.

## License-free checks

```text
python -m pytest
```

The test suite validates the common contract, adapter mappings, dry-run
Lumerical templates, synthetic canonical spectra, and cross-solver comparison.

## Real solver execution

Meep requires Linux/WSL and a compatible PyMeep environment. Lumerical requires
an installed API and explicit approval before a licensed FDTD session is
launched. Real solver runs are intentionally not started by the default test
suite.

After approved runs, compare canonical outputs with:

```text
python fdtd-core/benchmarks/compare_cross_solver.py \
  <meep-results>/spectra.npz <lumerical-results>/spectra.npz \
  --report cross-solver-report.json
```
