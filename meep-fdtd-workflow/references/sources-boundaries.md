# Sources, boundaries, symmetry, and periodicity

## Source selection

### Broadband spectrum

Use `mp.GaussianSource(fcen, fwidth=df)` when one transient simulation should
cover a band. Confirm the useful source spectrum covers all DFT frequencies.
Increase source `cutoff` if residual source truncation limits a strict decay
criterion.

### Continuous wave

Use `mp.ContinuousSource(frequency=f)` for steady-state visualization. Run until
transients decay, or use `sim.solve_cw(...)` for a suitable linear problem.

### Waveguide mode

Use `mp.EigenModeSource` to launch a controlled guided mode. Specify mode band,
parity, direction, and eigenmode tolerances explicitly. It couples to MPB and
must be treated as an advanced dependency.

### Plane wave

An extended source plus a Bloch vector can generate an oblique/periodic plane
wave. If the source extends into PML, set `is_integrated=True` as documented.

### Custom and beam sources

Use `CustomSource` only when a standard source cannot represent the temporal
profile. Use Gaussian beam sources for a finite beam, not a plane-wave source
with an arbitrary envelope.

## PML and absorber

PML lies inside the declared cell. Physical measurements should be taken in
the non-PML interior.

Starting rule:

```text
PML thickness ~ half of the largest relevant wavelength
```

This is only a starting point. Double PML thickness until the requested
observable converges.

Keep sufficient ordinary material between a resonant/evanescent structure and
PML. Otherwise the PML produces artificial loss.

Use or test `mp.Absorber` when:

- the medium varies in the boundary-normal direction;
- a periodic/oblique waveguide crosses the absorber;
- a backward-wave or plasmonic mode makes PML unstable;
- dispersive material overlapping PML diverges.

## Boundary condition by direction

For each axis, declare exactly one physical intent:

- open/radiating: PML or absorber;
- periodic/Bloch: periodic boundary plus `k_point`;
- mirror/rotation reduced: `symmetries`;
- conductor: default boundary behavior where appropriate.

Do not add PML in a direction meant to be periodic.

## Symmetry

`mp.Mirror(direction, phase=+1 or -1)` reduces the cell only if geometry,
materials, source, requested mode, and monitors transform consistently.

Meep cannot infer that a user's symmetry phase is physically correct. Validate
one smaller case without symmetry. A wrong parity can suppress the desired
mode while producing a numerically clean result.

## Bloch periodicity

Use `k_point` for a periodic cell with Bloch phase. A nonzero Bloch vector
generally requires complex fields. Ensure source and monitor interpretation
matches a unit-cell calculation.

For band diagrams, use a controlled list of k points and compare selected
points against an independent run or MPB where appropriate.

## Placement rules

- Keep sources and monitors outside PML.
- Keep a reflection monitor between source and scatterer.
- Keep a transmission monitor beyond the scatterer but before PML.
- For two-run reflection subtraction, preserve source, monitor, cell,
  resolution, Courant, and time profile exactly.
- Avoid placing a decay probe at a symmetry-enforced field node.
- A near2far surface must enclose all relevant radiators and use correct
  outward-normal weights.

## Source anchors

- `../../meep-master/python/source.py`
- `../../meep-master/python/simulation.py`
- `../../meep-master/doc/docs/Perfectly_Matched_Layer.md`
- `../../meep-master/doc/docs/Exploiting_Symmetry.md`
- `../../meep-master/python/examples/oblique-planewave.py`
- `../../meep-master/python/examples/wvg-src.py`
