# Modeling API and implementation map

## High-level model

The Python `Simulation` object is the workflow boundary:

```python
sim = mp.Simulation(
    cell_size=cell,
    geometry=geometry,
    sources=sources,
    boundary_layers=boundaries,
    resolution=resolution,
)
```

Common model objects:

- `mp.Vector3`: positions, sizes, lattice vectors, and Bloch vectors.
- `mp.Medium`: nondispersive, dispersive, anisotropic, conductive, nonlinear,
  or magnetic material.
- `mp.Block`, `Sphere`, `Cylinder`, `Prism`: geometric objects.
- `default_material`: background material.
- `material_function`: position-dependent material callback.
- `mp.materials`: predefined fitted materials; verify their valid frequency
  range before use.

Later geometry entries override earlier entries in overlap regions. Use this
deliberately for holes and inclusions.

## Dimensions

- 1D: only one nonzero cell dimension.
- 2D Cartesian: `mp.Vector3(sx, sy, 0)`.
- 3D: all cell dimensions nonzero.
- cylindrical: set cylindrical dimensions and azimuthal index `m`.

Do not obtain a 3D quantitative result from a 2D effective-index model without
documenting the approximation.

## Material rules

- Use real positive `epsilon`/`index` for nondispersive dielectrics.
- Use Lorentz/Drude susceptibilities or `mp.materials` for broadband loss and
  metals.
- Do not specify a frequency-independent complex permittivity as though it were
  a stable broadband time-domain material.
- A narrow-band imaginary permittivity may be represented through conductivity
  with the documented conversion.
- Check every material model over the entire source/monitor band, not only at
  its center.
- If a material callback returns dispersive media, provide representative
  `extra_materials` when required by the API.

## Initialization behavior

The Python constructor stores a high-level description. `init_sim()` or the
first `run()` creates C++ structures and fields:

```text
Simulation
  -> grid volume, symmetry, boundary region
  -> create_structure through SWIG
  -> geometry/material assignment
  -> C++ fields object
  -> source registration
  -> time stepping and DFT accumulation
```

Changing geometry after initialization does not silently rebuild every C++
object. Create a new `Simulation` or call the documented reset/reinitialization
path.

## Source-code anchors

- `../../meep-master/python/simulation.py`: `Simulation`, initialization,
  monitor APIs, run control, output.
- `../../meep-master/python/geom.py`: `Vector3`, `Medium`, geometric objects,
  material grids.
- `../../meep-master/python/materials.py`: predefined material fits.
- `../../meep-master/python/meep.i`: SWIG helpers such as structure creation and
  material transfer.
- `../../meep-master/python/typemap_utils.cpp`: Python geometry conversion.
- `../../meep-master/src/meepgeom.cpp`: continuous geometry to grid material.
- `../../meep-master/src/meep.hpp`: C++ `structure`, `fields`, and DFT classes.
- `../../meep-master/src/step.cpp`: one complete FDTD update.

## Modeling checklist

Before generating code, state:

1. coordinate system and dimensional approximation;
2. physical-to-Meep length conversion;
3. material model and valid band;
4. smallest material wavelength and smallest feature;
5. domain, padding, and boundary condition per direction;
6. required field component and symmetry parity;
7. target observable and its monitor.
