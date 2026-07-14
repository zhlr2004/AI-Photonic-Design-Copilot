# Requirement intake

Complete this contract before choosing a template. Mark unknown items and ask
only questions that materially change the model.

## Physical problem

- [ ] Objective stated in one sentence.
- [ ] Requested observables identified: fields, R/T, S parameters, Q, LDOS,
      force, radiation pattern, band structure, or optimization objective.
- [ ] Physical geometry and dimensional approximation documented.
- [ ] Coordinate system selected: Cartesian 1D/2D/3D or cylindrical.
- [ ] Polarization/field components specified.

## Units and spectrum

- [ ] Physical length unit `a` selected.
- [ ] Wavelength/frequency range and sampling count specified.
- [ ] Source center, bandwidth, profile, position, and direction specified.
- [ ] Required spectral resolution or time-domain duration specified.

## Materials

- [ ] Background and every object material identified.
- [ ] Nondispersive, dispersive, lossy, gain, nonlinear, or anisotropic behavior
      identified.
- [ ] Source of material parameters and valid spectral range recorded.
- [ ] Temperature/fabrication assumptions recorded if relevant.

## Boundaries and ports

- [ ] Physical intent declared independently for X, Y, and Z boundaries.
- [ ] Open directions, periodicity/Bloch vector, conductor, and symmetry stated.
- [ ] Input/output ports or radiation surfaces defined.
- [ ] Normalization/reference structure defined for scattering calculations.

## Accuracy and resources

- [ ] Target quantity and numerical tolerance declared.
- [ ] Required validation identified: analytic, energy balance, reference data,
      cross-method, or convergence only.
- [ ] Available memory, physical cores, and maximum runtime stated.
- [ ] Serial versus MPI execution selected.

## Output contract

- [ ] Required raw arrays and complex phase data listed.
- [ ] Required plots listed.
- [ ] HDF5/NPZ/JSON output preference stated.
- [ ] Parameter-sweep dimensions and naming convention stated.

## Assumptions requiring confirmation

List each proposed default with its physical consequence:

```text
Assumption:
Reason:
Consequence:
Accepted by:
```
