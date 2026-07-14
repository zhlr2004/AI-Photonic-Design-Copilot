# Sources and boundaries

## Source selection

Choose the source from the physical excitation and observable:

- **Plane wave/Gaussian beam**: free-space illumination, multilayers, gratings,
  and scattering.
- **Mode source/port**: guided-wave devices and modal S parameters.
- **Dipole**: spontaneous-emission, LDOS, cavity, and antenna studies.
- **TFSF**: scattering cross sections when incident and scattered fields must be
  separated.
- **Imported/custom field**: measured or externally computed beams with an
  explicit normalization convention.

Set injection axis, direction, position, transverse span, wavelength/frequency
band, phase, and polarization or mode selection explicitly. Ensure the source
span covers the intended aperture or mode without entering PML.

## Mode sources

- Put the source in a uniform waveguide section.
- Record mode order, polarization/fraction selection, and direction.
- Check the selected mode at several wavelengths for broadband work.
- Distinguish solver mode numbering from a physical TE/TM label.
- Verify the source plane does not overlap a discontinuity or evanescent near
  field from the device.

## Open boundaries and PML

- Use PML only for physically open directions.
- Keep structures, sources, and monitors away from PML unless the documented
  method requires an overlap.
- Provide enough homogeneous or smoothly varying padding for outgoing fields.
- Increase PML layers and padding independently during convergence testing.
- For metals, steep angles, periodic media, or strong evanescent fields, test
  available PML formulations rather than assuming the default is adequate.

## Periodic and Bloch boundaries

- Model a single cell only when geometry and excitation are periodic.
- Pair periodic boundaries on the same axis.
- Use Bloch phase consistently with incidence angle, wavelength, and lattice
  vector.
- Do not put PML on a periodic axis.
- For broadband oblique incidence, verify whether the chosen source/boundary
  formulation preserves the intended angle across frequency.
- Include all propagating diffraction orders in energy checks.

## Symmetry and metallic boundaries

- Symmetric/antisymmetric boundaries impose field parity, not merely geometric
  mirroring.
- Check geometry, source polarization, phase, and every requested monitor
  quantity before reducing the domain.
- Validate one representative case without symmetry.
- Use PEC/PMC/metal boundaries only when they represent the physical problem or
  a justified symmetry condition.

## Placement checks

- [ ] Source and monitors are outside PML
- [ ] Monitor planes do not intersect unintended structures
- [ ] Mode planes lie in uniform ports
- [ ] Source spectrum covers monitor sampling
- [ ] Direction and normal conventions are recorded
- [ ] Boundary pairs and symmetry parities are consistent
- [ ] Padding separates PML from reactive/evanescent fields

An apparently clean field plot does not prove that reflections from a boundary
or mode mismatch are negligible.
