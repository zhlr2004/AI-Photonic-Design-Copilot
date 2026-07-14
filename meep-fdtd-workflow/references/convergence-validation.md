# Convergence and physical validation

## A result is not converged by default

Define before running:

- target observable;
- reference scale used for relative error;
- acceptable numerical change;
- physics check and tolerance;
- maximum resource budget.

The tolerance depends on the problem. Do not claim a universal number.

## Minimum convergence matrix

Vary independently:

1. **Resolution**: increase pixels per unit length while preserving physical
   geometry and monitor positions.
2. **Boundary absorption**: increase PML/absorber thickness and, when relevant,
   ordinary padding from the structure.
3. **Run control**: tighten decay threshold or extend ring-down.

For each case store the observable and compute:

```text
relative_change = norm(new - previous) / max(norm(new), small_floor)
```

For spectra, compare both an aggregate norm and important peaks/dips.

Do not change multiple convergence variables simultaneously if the goal is to
identify the dominant error.

## Problem-specific checks

### Passive lossless scattering

- Verify finite spectra and a nonzero incident normalization.
- Check `R >= 0`, `T >= 0` within numerical tolerance.
- Check `R + T` plus all other propagating channels is near one.
- A reported `1-R-T` is absorption only if every outgoing channel is captured.

### Mode decomposition

Compare power from eigenmode coefficients with the flux monitor. Include every
propagating band/order needed for energy balance.

### Near-to-far

Compare near2far output with a direct DFT field on a test surface or against an
analytic radiation pattern. Check integrated far-field power against near-field
flux.

### Resonators

Check resonant frequency and Q across resolution, PML/padding, ring-down, source
position, and probe position. High-Q modes are especially sensitive to PML
overlap with evanescent fields.

### Periodic structures

Check reciprocal/symmetry-related k points when applicable. Increase supercell
size if a nominally isolated defect interacts with periodic copies.

### Dispersive materials

Evaluate the implemented `epsilon(f)` over the entire band. Compare a simple
interface with Fresnel theory or a known dispersion relation before using the
material in a complex geometry.

### Adjoint optimization

Before optimization, compare an adjoint directional derivative with finite
differences:

```text
adjoint_dd = direction dot gradient
finite_difference_dd = F(x + step*direction) - F(x)
```

Repeat at more than one step size to distinguish truncation and numerical
noise.

## Symmetry validation

Run one affordable case with and without symmetry. Compare the same physical
observable after accounting for domain multiplicity and monitor weights.

## Validation record

Save a machine-readable record containing:

- parameter values for every convergence case;
- raw observable arrays;
- relative changes;
- declared thresholds;
- pass/fail per criterion;
- warnings and excluded frequencies;
- completion state.

The provided `../scripts/validate_results.py` handles generic finite-value,
frequency-axis, R/T-balance, and convergence-difference checks. It cannot
decide whether the physical model is correct.

## Source anchors

- `../../meep-master/doc/docs/FAQ.md`
- `../../meep-master/doc/docs/Subpixel_Smoothing.md`
- `../../meep-master/tests/2D_convergence.cpp`
- `../../meep-master/python/tests/test_bend_flux.py`
- `../../meep-master/python/tests/test_mode_decomposition.py`
- `../../meep-master/python/tests/test_cavity_farfield.py`
- `../../meep-master/python/tests/test_adjoint_solver.py`
