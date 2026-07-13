# Physics Paper Figure Reproduction

Reproduce `<target figures/panels>` from the supplied paper. Every requested
result must be generated from a model constructed and solved inside a suitable
numerical simulator through its API or simulation library. Outputs will be
checked for completeness, physical validity, convergence, and agreement with
the paper.

---

## 1. Article Information

| Field | Value |
| --- | --- |
| **Title** | `<paper title>` |
| **Authors** | `<authors>` |
| **DOI** | `<DOI or "not provided">` |
| **Paper File** | `<task-root-relative paper Markdown path>` |
| **Target Figures** | `<figure and panel identifiers>` |

---

## 2. Core Directives

| Directive | Requirement |
| --- | --- |
| **Evidence First** | Trace geometry, materials, sources, solver settings, and target values to the paper, supplement, or a clearly labeled assumption. Never present an assumption as a paper fact. |
| **Simulation Mandatory** | Use a suitable simulator API or simulation library to construct and solve the paper's physical model. A GUI-only or analytical-only workflow is insufficient. |
| **Model Fidelity** | Programmatically build the reported geometry, materials, sources, boundaries, discretization, monitors/probes, and parameter sweeps inside the selected simulator. |
| **Data Provenance** | Final CSV and PNG outputs must derive from exported solver results and remain traceable to a model/configuration and solver run. |
| **Code Integrity** | Do not hardcode, trace, digitize, fit, or analytically synthesize the requested answer and present it as simulated output. |
| **Visualization** | Produce publication-quality plots with correct units, axes, normalization, labels, and panel layout. |
| **Validation** | Check convergence, physical constraints, limiting cases, and panel-specific numerical or visual agreement. Rerun the simulation after correcting any mismatch. |

---

## 3. Interactive Workflow

### Step 1: Verify Inputs

- Confirm the paper Markdown and `images/` directory exist in the task root.
- Confirm all referenced paper images resolve and identify the source image for
  every target panel.
- Read the main text, methods, captions, equations, tables, and supplementary
  information relevant to the targets.

### Step 2: Extraction and Hard-Logic Verification

Do not start implementation until this step is complete.

| Task | Requirement |
| --- | --- |
| **Identify Targets** | List every requested figure/panel, its physical observable, and its stable output basename, such as `fig2_b`. |
| **Parameter Provenance** | Record every required parameter, value, unit, and source location. Mark missing values as unspecified. |
| **Model Definition** | Extract geometry, coordinate system, materials, dispersion/loss, sources, boundaries, domain, discretization, monitors/probes, sweeps, and solver stopping criteria. |
| **Target Data** | Extract explicit values, ranges, peaks, signs, symmetries, normalization, and other validation evidence from the paper. |
| **Derived Quantities** | Record equations allowed for post-processing exported solver data. |
| **Limiting Cases** | Define analytical or physical limits that test the implementation without replacing the simulation. |
| **Missing Data Strategy** | State each justified assumption, its basis, and the sensitivity or convergence check needed to assess it. |

### Step 3: Select the Simulator and Plan the Implementation

Create `reproduction/plan.md` before coding. It must contain:

- the selected numerical method, simulator, API/library, and selection rationale;
- installation, license, version, and runtime requirements;
- a mapping from paper parameters to simulator objects and units;
- model-construction and solve pseudocode;
- mesh/basis/time-step/domain convergence strategy;
- parameter-sweep and result-export strategy;
- assumptions, risks, expected resource cost, and recovery/checkpoint behavior.

Choose the simulator from the target physics and the paper's method. Prefer a
maintained, automatable tool from the skill's preferred simulator list when
technically suitable. A tool outside that list is allowed when its use is
justified and it exposes a reliable API, library, scripting, or batch interface.
If multiple tools satisfy the technical requirements, check their local/API and
license or service availability before selecting one; record the result without
installing software, activating licenses, or submitting paid/cloud jobs solely
for this check.
Replace this guidance in the completed instruction with the selected tool,
method, API/library, and concrete requirements so the instruction is
self-contained.

### Step 4: Implement with Separation of Concerns

| Component | Requirement |
| --- | --- |
| **Simulation/Compute Code** | Under `reproduction/`, use the selected API/library to create the full model inside the simulator, run the real numerical solver, save the model/configuration, and export raw and tabular results. Do not render final figures here. |
| **Plot Code** | Under `reproduction/`, read only simulation-derived exported data and render the requested panels. Do not reconstruct target data from analytical formulas. |
| **Shared Utilities** | Centralize units, provenance, file naming, validation, and simulator-session helpers without hiding the model definition. |

The automation must be reproducible from a clean simulator session. Opening a
prebuilt project and merely exporting its existing results does not satisfy the
model-construction requirement.

### Step 5: Run Simulations and Generate Data

For each target basename `<panel>`:

1. Create the geometry, materials, sources, boundaries, discretization, and
   monitors/probes through the simulator API or library.
2. Save `data/<panel>.<native-model-extension>`. If the solver has no project
   format, save a complete executable model/configuration.
3. Run the solver and save native raw result files where appropriate.
4. Export plotting data to `data/<panel>.csv`.
5. Render the final panel as `data/<panel>.png`.

Keep final deliverables directly under `data/` unless the task specifies another
layout. Temporary runs may use `test/`, but they are not final deliverables.

### Step 6: Anti-Cheat and Consistency Audit

Before finalizing, verify:

- the code builds the required structure inside the simulator rather than only
  making nominal API calls;
- the selected numerical solver actually ran for every required configuration;
- every final value can be traced to exported solver data;
- no hardcoded targets, traced images, analytical fields, synthetic fields, or
  precomputed answers are used as simulation output;
- digitized paper data, if used, is labeled only as validation ground truth;
- units, materials, geometry, boundaries, sources, discretization, normalization,
  and post-processing match the evidence table;
- filenames and target identifiers agree across code, models, CSV, PNG,
  validation, and deliverables.

If a result mismatches the paper, inspect the evidence and implementation,
correct the model or post-processing, rerun the solver, and regenerate outputs.

### Step 7: Document the Reproduction

Create `reproduction/ANALYSIS.md` containing:

- theory and target-observable summary;
- parameter provenance and assumptions;
- simulator and method rationale;
- model-construction and numerical settings;
- convergence and validation results;
- reproduced figures and quantitative comparisons;
- limitations, discrepancies, and resource requirements.

---

## 4. Coding Guidelines

- Use the selected simulator's supported API/library and stable scientific
  computing dependencies.
- Keep units explicit and convert them at well-defined boundaries.
- Make runs deterministic where the solver permits and record random seeds.
- Add assertions for physical constraints and exported array shapes/units.
- Parameterize paper values instead of scattering constants through the code.
- Log simulator version, model settings, run status, and output provenance.
- Fail clearly when the simulator, license, dependency, or expected result is
  unavailable; do not silently substitute analytical data.

---

## 5. Data Files to Reproduce

### `<Figure/panel group and physical observable>`

**Target basenames:** `<fig1_a, fig1_b, ...>`

**Required model and setup:**

- Geometry: `<paper-derived geometry and dimensions>`
- Materials: `<models, dispersion, loss, temperature>`
- Sources: `<type, wavelength/frequency, polarization, phase, amplitude>`
- Domain and boundaries: `<dimensionality, extents, boundary conditions>`
- Discretization: `<mesh/basis/time step and refinement requirements>`
- Monitors/probes: `<locations and exported quantities>`
- Parameter sweep: `<values and mapping to target panels>`
- Post-processing: `<operations applied only to exported solver results>`

**Required files per basename:**

- `data/<basename>.<native-model-extension>` or complete model/configuration;
- `data/<basename>.<native-raw-result-extension>` when applicable;
- `data/<basename>.csv`;
- `data/<basename>.png`.

Repeat this subsection for every materially different figure or simulation
configuration.

---

## 6. Banned Practices

- Bypassing the simulator with analytical, synthetic, surrogate, or manually
  constructed final fields or observables.
- Hardcoding target arrays, pixels, peaks, fitted curves, or expected answers.
- Presenting digitized paper data as newly simulated data.
- Calling an API without constructing and solving the paper-required model.
- Reusing a supplied solved project as the final result without programmatic
  reconstruction.
- Plotting directly from formulas when the requested result is a simulation
  observable.
- Hiding missing parameters or unsupported assumptions.

Analytical formulas remain allowed for geometry/source definitions,
paper-specified post-processing of exported data, limiting-case checks, and
independent validation.

---

## 7. Validation Requirements

| Check | Target |
| --- | --- |
| **Completeness** | Every target has a model/configuration, solver-derived CSV, final PNG, and any required raw result. |
| **Convergence** | Demonstrate suitable mesh/basis/time-step/domain convergence for the chosen method. |
| **Physical Validity** | Check applicable conservation laws, reciprocity, causality, symmetry, passivity, units, and limiting cases. |
| **Numerical Agreement** | Use paper-supported error thresholds when quantitative target data exists. |
| **Visual Agreement** | Otherwise require non-trivial, physically plausible agreement in morphology, peaks, signs, symmetry, scale, and axes. |
| **Traceability** | Record which model run and exported dataset produced each CSV and PNG. |

Document normalization and any physically equivalent rotations, reflections, or
phase conventions. Never use them to conceal a genuine mismatch.

---

## 8. Deliverables

| Deliverable | Path |
| --- | --- |
| Implementation Plan | `reproduction/plan.md` |
| Simulation/Compute Code | `reproduction/<target>_compute.<ext>` |
| Plot Code | `reproduction/<target>_plot.<ext>` |
| Native Models/Configurations | `data/<basename>.<native-model-extension>` |
| Native Raw Results | `data/<basename>.<native-raw-result-extension>` when applicable |
| Plotting Data | `data/<basename>.csv` |
| Final Figures | `data/<basename>.png` |
| Analysis Document | `reproduction/ANALYSIS.md` |

(End of file)
