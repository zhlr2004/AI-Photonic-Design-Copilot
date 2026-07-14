# Environment and units

## Python API selection

Use the API shipped for the installed Lumerical release. Prefer:

```python
import ansys.lumerical.core as lumapi
```

If unavailable, use the traditional installation-provided module:

```python
import lumapi
```

Do not install an unrelated package named `lumapi` from a public package index.
For traditional installations, add the documented API directory to
`PYTHONPATH` or `sys.path`; do not copy `lumapi.py` and native libraries into
the project. Record the resolved module path.

Run:

```text
python scripts/verify_environment.py
```

This checks importability without opening FDTD. To test session creation,
version retrieval, and license access, obtain user permission and run:

```text
python scripts/verify_environment.py --launch-session
```

Session launch consumes a license seat and may open a GUI unless hidden mode is
supported and selected.

## Session lifecycle

Prefer explicit cleanup:

```python
with lumapi.FDTD(hide=True) as fdtd:
    # configure, save, run, and retrieve results
    pass
```

If the installed API does not support the context-manager pattern, close the
session in `finally`. Never leave a session open after an exception.

## Units

- Python API geometry, wavelength, mesh, and spatial coordinates use SI units.
- Lumerical datasets may expose frequency in hertz and wavelength in metres.
- Convert only at input/output boundaries, for example `um = 1e-6` and
  `nm = 1e-9`.
- Label converted axes; never infer micrometres from an unlabeled number.
- Use vacuum relations consistently: `f = c / wavelength` and
  `omega = 2*pi*f`.
- Check whether imported material data uses wavelength, frequency, angular
  frequency, energy, or a solver-specific convention.

## Version and license record

Record:

- OS, Python version, executable, and architecture;
- API flavor and module path;
- FDTD version/build returned by the installed API;
- local or remote/interop execution;
- GUI/hidden mode;
- license error text without exposing server credentials.

## Resource estimate

Before a 3D run:

1. Estimate grid cells from the FDTD region and effective mesh spacing.
2. Account for field components, dispersive auxiliary variables, monitors, and
   conformal mesh overhead.
3. Treat frequency-domain profile monitors as potentially large datasets.
4. Keep headroom for the application, Python, exported arrays, and file saving.
5. Test one reduced case before a sweep or optimization.

Do not use successful API import as proof that an FDTD license is available.
