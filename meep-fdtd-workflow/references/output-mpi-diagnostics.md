# Output, MPI, and diagnosis

## Output strategy

Use:

- `get_array`: real-time field/material slice as a NumPy array;
- `get_dft_array`: complex field at a DFT frequency;
- `get_fluxes`/mode coefficients: compact spectral observables;
- Meep `output_*`: HDF5 field/material output;
- NPZ: related NumPy arrays and metadata;
- JSON: scalar parameters, versions, checks, and file manifest.

Save frequency and wavelength axes explicitly. Preserve complex data; do not
save only magnitudes if phase may matter.

Use separate directories for raw data, derived data, figures, and logs. Record
the command and source script with every result.

## MPI

Install and run the MPICH Conda build:

```bash
conda create -n pmp -c conda-forge "pymeep=*=mpi_mpich_*"
conda activate pmp
mpirun -np 4 python -m mpi4py simulation.py
```

The `-m mpi4py` form helps abort the whole job if one rank fails.

Rules:

- Do not use more MPI processes than physical cores without evidence.
- Parallel Meep is not supported interactively in a notebook.
- Every rank executes the script.
- Meep simulation operations are collective and must be called in identical
  order on every rank.
- Guard only ordinary external plotting/file work:

```python
if mp.am_master():
    np.savez("results.npz", ...)
```

- Do not place `sim.run`, `get_array`, or other collective Meep operations
  inside `if mp.am_master()`.
- Try `split_chunks_evenly=False` only as a measured load-balancing experiment.

For independent cases, use `divide_parallel_processes` and
`merge_subgroup_data`. Only the overall master should write merged results.

## Diagnosis order

### Import, crash, or illegal instruction

- Confirm WSL/Linux and active Conda environment.
- Unset unrelated `PYTHONPATH`.
- Confirm Meep, NumPy, BLAS, MPI, and HDF5 came from compatible channels/builds.
- Run `../scripts/verify_environment.py`.

### Fields diverge

- Check units and source band.
- Check instantaneous epsilon is positive where required.
- Check Lorentz/Drude pole frequencies against the time step.
- Reduce Courant or increase resolution.
- Replace overlapping dispersive-PML regions with a tested absorber.
- Distinguish intended gain from numerical instability.

### PML reflection or artificial loss

- Double PML thickness.
- Increase ordinary padding from evanescent fields.
- Check medium variation normal to PML.
- Test `Absorber` for periodic/oblique/backward-wave media.
- Never interpret fields inside PML as physical output.

### R/T is unphysical

- Confirm reference and device grids/source/monitor positions are identical.
- Subtract incident fields only at the reflection plane.
- Confirm monitor normal/sign convention.
- Capture all propagating ports/orders and real absorption.
- Tighten decay and inspect low-incident-power frequencies.

### Resonances are unstable

- Move source/probe away from field nodes.
- Change source symmetry to test mode overlap.
- Increase ring-down and padding.
- Compare without symmetry.
- Treat isolated spurious Harminv modes cautiously.

### MPI hangs

- Look for one rank that threw an exception.
- Ensure all ranks call Meep collectives in the same order.
- Keep external I/O on master, not Meep API calls.
- Confirm every rank can access scripts and HDF5 paths.

## Source anchors

- `../../meep-master/doc/docs/Parallel_Meep.md`
- `../../meep-master/doc/docs/Installation.md`
- `../../meep-master/doc/docs/Materials.md`
- `../../meep-master/doc/docs/Perfectly_Matched_Layer.md`
- `../../meep-master/python/tests/test_divide_mpi_processes.py`
- `../../meep-master/src/h5fields.cpp`
