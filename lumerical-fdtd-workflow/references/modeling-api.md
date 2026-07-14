# Modeling with the Python API

## Object model

A typical script owns one FDTD session and creates named objects:

1. FDTD simulation region;
2. geometry and structure groups;
3. mesh overrides;
4. sources;
5. monitors and analysis objects;
6. sweeps or optimization definitions.

Most Lumerical script commands are exposed as session methods. Depending on the
API release, an `add...` method may accept keyword arguments, a `properties`
mapping, or require follow-up `set`/`setnamed` calls. Confirm exact names against
the installed documentation.

## Stable construction pattern

- Clear or create a known project state; do not append silently to an unknown
  interactive session.
- Give every object a unique, stable name.
- Group configuration into parameters, model construction, monitors, run, and
  export functions.
- Prefer returned object handles when the API supports them.
- Otherwise use `setnamed` rather than relying on the currently selected object.
- Save the project before running.

Some properties depend on earlier properties. For example, an override flag may
need to be enabled before setting a frequency-point count. Use
`collections.OrderedDict` or explicit sequential assignments when order matters.

## Geometry

- Express Python coordinates and spans in metres.
- Define a clear origin and propagation-axis convention.
- Distinguish object centre/half-span from min/max definitions.
- Avoid zero-thickness 3D objects unless the solver object explicitly supports
  a sheet/surface model.
- Parameterize fabrication dimensions separately from numerical padding.
- Inspect imported GDS/CAD layer mapping, scale, origin, and z extrusion.

## Materials

- Prefer a documented entry from the installed material database when it
  matches the intended process and band.
- Record material names exactly as used in the project.
- For sampled or fitted data, preserve the source, units, interpolation, fit
  range, and passivity assumptions.
- Confirm anisotropy axes and tensor orientation.
- Do not replace dispersive loss with a broadband constant complex index unless
  the approximation is requested and its valid range is justified.
- Validate a custom material on a simple interface before complex geometry.

## FDTD region and mesh

- Include geometry, propagation distance, monitor/reference planes, padding,
  and PML.
- Use global mesh accuracy for a baseline and local mesh overrides for small
  features, interfaces, gaps, metals, and sensitive design regions.
- Avoid a mesh override that accidentally excludes a critical interface.
- Check conformal-mesh behavior for metals, thin layers, and staircased edges.
- Treat mesh order/material priority as part of the physical model.

## Script organization

Generated code should preserve:

```text
parameters
session
model
preview
monitors
save
run
validate
export
```

Store tunable values once. Avoid embedding LSF strings in Python when equivalent
API methods are clear; use `eval` only when a solver-native command/function is
needed, and keep the evaluated script auditable.

## Modeling review

- [ ] Object names are stable and unique
- [ ] Units and coordinate convention are documented
- [ ] Geometry and material precedence are visually inspected
- [ ] Material validity covers the source band
- [ ] FDTD region and mesh resolve all relevant structures
- [ ] Order-dependent properties are assigned safely
- [ ] Saved `.fsp` reproduces the scripted state
