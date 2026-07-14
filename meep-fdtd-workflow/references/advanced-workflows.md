# Advanced workflows

Use this reference only after the basic model passes preflight.

## Dispersive and lossy materials

- Prefer a documented material fit from `mp.materials` or explicit
  Lorentzian/Drude susceptibilities.
- Verify the fit's valid frequency range and units.
- The instantaneous `epsilon` must satisfy the model's stability requirements.
- Material poles add auxiliary fields, memory, and stability constraints.
- Only the nondispersive part receives Meep's full subpixel averaging.
- Validate a material on a planar interface or dispersion test before complex
  geometry.

References:
`../../meep-master/doc/docs/Materials.md`,
`../../meep-master/python/examples/material-dispersion.py`, and
`../../meep-master/python/examples/eps_fit_lorentzian.py`.

## Modal sources and S parameters

Use `EigenModeSource` and `get_eigenmode_coefficients` for guided ports.
Explicitly set:

- mode band/index and parity;
- propagation direction;
- eigensolver resolution/tolerance;
- monitor cross section in a uniform port;
- forward/backward coefficient convention.

Validate modal power against flux. Include all propagating bands when checking
energy conservation.

Reference: `../../meep-master/python/examples/mode-decomposition.py`.

## Periodic and diffractive structures

- Model one unit cell with a Bloch `k_point`.
- Apply PML only in nonperiodic open directions.
- For diffraction, enumerate propagating orders and include their power.
- Confirm angle, Bloch vector, and frequency use a consistent convention.
- Check energy balance across all reflected/transmitted orders.

References:
`../../meep-master/python/examples/binary_grating.py` and
`../../meep-master/python/examples/refl-angular.py`.

## Near-to-far transformation

- Build a closed near-field surface around radiators/scatterers.
- Set region weights according to outward normals.
- Keep the surface outside sources/structure but inside PML.
- Use enough angular points for integrated power.
- Compare a reduced case against direct DFT fields or an analytic pattern.

Reference: `../../meep-master/python/examples/cavity-farfield.py`.

## Resonances and MPB

Use Harminv for lossy/open resonances and MPB for lossless periodic eigenmodes
when MPB is better conditioned. Harminv can miss a mode orthogonal to the
source or merge close modes; repeat with another source/probe.

References:
`../../meep-master/python/examples/ring.py` and
`../../meep-master/python/examples/mpb_tutorial.py`.

## Cylindrical coordinates

Use cylindrical coordinates only for true azimuthal decomposition. Specify the
azimuthal index `m`, account for complex fields when `m != 0`, and validate the
axis behavior and radial PML separately.

References:
`../../meep-master/python/examples/ring-cyl.py` and
`../../meep-master/python/tests/test_pml_cyl.py`.

## Frequency-domain solve

For one linear frequency, `solve_cw` may be more efficient than waiting for a
continuous source. Check solver tolerance, maximum iterations, and agreement
with a transient/DFT case before using it as the production path.

Reference: `../../meep-master/python/examples/solve-cw.py`.

## MPI parameter sweeps

Two distinct uses:

1. spatial decomposition: all ranks solve one large simulation;
2. subgroup sweep: `divide_parallel_processes(N)` assigns independent cases.

Set identical random seeds on every rank for optimization. Use
`am_really_master()` for final merged external output.

Reference:
`../../meep-master/python/tests/test_divide_mpi_processes.py`.

## Adjoint optimization

Optimization is not a substitute for a validated forward model.

1. Validate source, ports, objective, and convergence in a fixed design.
2. Define `MaterialGrid` and design region.
3. Apply filtering/projection consistently.
4. Verify an adjoint directional derivative with finite differences.
5. Optimize with deterministic initialization and saved checkpoints.
6. Re-evaluate the final design at higher resolution and tighter convergence.

References:
`../../meep-master/python/adjoint/`,
`../../meep-master/python/examples/adjoint_optimization/`, and
`../../meep-master/python/tests/test_adjoint_solver.py`.
