# Environment and units

## Supported runtime

Use Linux or WSL2. The local Meep documentation states that native Windows is
unsupported (`../../meep-master/doc/docs/Installation.md`).

Serial environment:

```bash
conda create -n mp -c conda-forge pymeep numpy matplotlib h5py
conda activate mp
python -c "import meep as mp; print(mp.__version__)"
```

MPI environment:

```bash
conda create -n pmp -c conda-forge "pymeep=*=mpi_mpich_*" numpy matplotlib h5py
conda activate pmp
mpirun -np 4 python -m mpi4py simulation.py
```

Use `conda-forge` consistently. An environment that mixes incompatible BLAS,
MPI, or HDF5 builds can import successfully and still fail later. Unset a
foreign `PYTHONPATH` when diagnosing imports.

Run `../scripts/verify_environment.py` before production work.

## Meep units

Meep sets the speed of light to one. Select one length unit `a`, for example
`a = 1 um`, and express every distance as a multiple of `a`.

For vacuum wavelength:

```text
lambda_meep = lambda_physical / a_physical
frequency_meep = 1 / lambda_meep
time_unit = a_physical / c
```

Meep frequency is `f`, not angular frequency `omega`; `omega = 2*pi*f`.

Example for `a = 1 um` and `lambda0 = 1.55 um`:

```python
length_unit_um = 1.0
wavelength_um = 1.55
wavelength = wavelength_um / length_unit_um
frequency = 1.0 / wavelength
```

Do not attach SI dimensions directly to Meep inputs. Record the conversion in
the result report.

## Resolution and time step

`resolution` is pixels per Meep length unit. For refractive index `n`, the
material wavelength is approximately `lambda0 / n`. Base the grid on the
shortest material wavelength and the smallest geometric feature.

The time step follows:

```text
dt = Courant / resolution
```

for the normalized Cartesian grid. The default Courant factor is 0.5. A
necessary stability condition is approximately:

```text
Courant < n_min / sqrt(number_of_dimensions)
```

Dispersive poles may require a smaller step. If a Lorentz pole is too fast for
the grid, increase resolution, reduce Courant, or change the material fit.

## Resource estimate

Before a 3D run, estimate:

```text
Nx ~= cell_x * resolution
Ny ~= cell_y * resolution
Nz ~= cell_z * resolution
grid_points = Nx * Ny * Nz
```

Doubling 3D resolution increases grid points by about eight and also increases
the number of time steps per physical duration by two. DFT monitors,
dispersive poles, complex fields, and PML add memory beyond the base field
arrays.

## Source anchors

- `../../meep-master/doc/docs/Installation.md`
- `../../meep-master/doc/docs/Introduction.md`
- `../../meep-master/doc/docs/Materials.md`
- `../../meep-master/doc/docs/FAQ.md`
