# Physics Paper Figure Reproduction

You are given a physics paper to reproduce. Your goal is to deeply understand the paper's theoretical framework and write rigorous, production-grade Python/Julia scientific computing code to reproduce its requested figures and data products. Target reproduction is restricted to Fig. 3(c) and Fig. 4(c); all requested figures must be generated and will be checked for presence, non-trivial content, and qualitative plausibility.

---

## 1. Article Information

| Field               | Value                                                        |
| ------------------- | ------------------------------------------------------------ |
| **Title**           | High-Order Nonlinear Spin-Orbit Interaction on Plasmonic Metasurfaces |
| **Author**          | Shumei Chen, Kingfai Li, Junhong Deng, Guixin Li, and Shuang Zhang |
| **DOI**             | 10.1021/acs.nanolett.0c03100; cite as Nano Letters 2020, 20, 8549-8555 |
| **Paper File**      | `High-Order Nonlinear Spin–Orbit Interaction on Plasmonic Metasurfaces.md` |

---

## 2. Core Directives

| Directive | Description |
| --------- | ----------- |
| **Accuracy First** | Never hallucinate parameters. Trace every constant to the text, captions, or standard literature. |
| **Code Integrity** | Do not "cheat" by hardcoding results. Implement the actual physical equations/algorithms. Don't take any practical shortcuts. |
| **Visualization** | Publication-quality plots (LaTeX labels, high DPI, correct axis scaling). |
| **Numerical Validation** | Code must reproduce the target SHG beam profiles for Gaussian-FW excitation in Fig. 3(c) and vortex-FW excitation in Fig. 4(c), including the q-dependent vortex rings and on-axis interference petals. Mismatches require immediate code revision. |
| **FDTD Data Source** | Final PNG and CSV outputs must be generated from electromagnetic field data exported by `lumapi`/Lumerical FDTD simulations, not from directly constructed analytical solutions. Analytical formulas may guide source setup, metasurface phase design, and validation, but electromagnetic fields must come from FDTD. |

---

## 3. Interactive Workflow

### Step 1: Input & Conversion
**Check first:** confirm the paper markdown file and the `images/` directory are present in the task root.
**Separate images:** the paper images are supplied as `images/fig1.png` through `images/fig4.png`. The required reproduction targets use `images/fig3.png` and `images/fig4.png`.


### Step 2: Extraction & "Hard Logic" Verification
*Crucial Step: Do not start coding until this analysis is complete.*

| Task | Description |
| ---- | ----------- |
| **Identify Targets** | Reproduce Fig. 3(c) and Fig. 4(c), split into nine q-indexed outputs each: `fig3c_1` through `fig3c_9` and `fig4c_1` through `fig4c_9`. |
| **Parameter Provenance Table** | Create a table mapping every symbol to its value and source (e.g., "$m_e$: 0.511 MeV (Page 3, Eq 2)"). |
| **Target Data Extraction** | Extract all explicit numerical values from text/captions and figure annotations to serve as ground truth for validation. This paper has q values, FW angular momentum states, SHG angular momentum selection rules, meta-atom dimensions, wavelength/NA values, and target vortex/interference beam profiles. |
| **Limiting Cases** | Define 1-2 analytical limits (e.g., "as $x \to 0$, $f(x)$ should approach $y$") to test the code against. |

### Step 3: Implementation Plan
Draft a plan in `reproduction/plan.md`:

| Item | Description |
| ---- | ----------- |
| **Methodology** | Lumerical FDTD simulation of nonlinear SHG from  $C_3$  plasmonic metasurfaces plus FDTD-field post-processing into far-field SHG beam profiles. |
| **Algorithm Pseudo-code** | Briefly map the computation loop. |
| **Missing Data Strategy** | How to handle unspecified parameters (e.g., "Assume $T=300K$ based on context"). |

### Step 4: Coding (Separation of Concerns)

| Component | Description |
| --------- | ----------- |
| **Compute Script** | Write the heavy-lifting physics logic. **NO PLOTTING HERE.** It must run/load `lumapi` FDTD results and export derived per-subfigure CSV data from simulated fields. |
| **Plot Script** | Import/load the FDTD-derived CSV data and render the figure. It must not synthesize final plot data from an analytical field model. |
| **Run Simulation** | Use `lumapi` with Lumerical FDTD to simulate and generate eighteen project files: `fig3c_1.fsp` through `fig3c_9.fsp` and `fig4c_1.fsp` through `fig4c_9.fsp`. This is mandatory for the new paper reproduction and is the only allowed source of final electromagnetic field data. Simulate SHG from gold  $C_3$  plasmonic metasurfaces with q-dependent nonlinear geometric phase under the target Gaussian-FW and vortex-FW excitations. |


**File Naming Convention:**
| File Type | Naming Format |
| --------- | -------------- |
| Compute Script | `reproduction/fig3c_compute.py`, `reproduction/fig4c_compute.py` |
| Plot Script | `reproduction/fig3c_plot.py`, `reproduction/fig4c_plot.py` |
| Simulation Files | `data/fig3c_1.fsp` through `data/fig3c_9.fsp`; `data/fig4c_1.fsp` through `data/fig4c_9.fsp` |
| Per-subfigure PNG | `data/fig3c_1.png` through `data/fig3c_9.png`; `data/fig4c_1.png` through `data/fig4c_9.png` |
| Per-subfigure CSV | Matching per-subfigure CSV files directly under `data/`, e.g., `data/fig3c_1.csv`, `data/fig3c_9.csv`, `data/fig4c_1.csv`, `data/fig4c_9.csv` |



### Step 5: Generate Data Files
Run your scripts to produce the eighteen `.fsp` files listed above, per-subfigure reproduced `.png` files, and per-subfigure plotting `.csv` data files directly under `data/` with no nested output folders. The electromagnetic-field PNG and CSV files must be generated from FDTD monitor data exported through `lumapi`. Any SHG near-field, far-field, vortex profile, and interference pattern must be derived from the FDTD-exported electromagnetic fields. See Section 5 for exact specifications.

### Step 5: The "Anti-Cheat" Audit & Consistency Check
*Self-Correction before finalizing:*

| Check | Description |
| ------| ----------- |
| **Algorithm Check** | Does the code actually run/load FDTD simulations and derive fields from FDTD monitor data? Reject hardcoded arrays and analytical-field stand-ins for final outputs. |
| **Numerical Consistency Check** | Compare every generated subfigure against the supplied target image panels for qualitative structure, non-trivial content, q-dependent vortex radius/order, Gaussian limit at zero OAM, interference petal counts, and sign conventions. Treat rotations as acceptable only when they are physically equivalent and documented. |
| **IF MISMATCH** | Stop. Re-read the theory. Check units, constants, and normalizations. Check logic. **Rewrite the compute code.** |

### Step 6: Documentation
Create `reproduction/ANALYSIS.md`:

| Item | Description |
| ---- | ----------- |
| **Author** | "RISE-AGI, Peking University" |
| **Content** | Brief theory summary, derivation steps, implementation details, figures, tables, and validation results. |
| **Limitation** | Honestly discuss any discrepancies or assumptions made. |

---

## 4. Coding Guidelines

### Libraries
| Library | Purpose |
| ------- | ------- |
| `numpy` | Numerical computing |
| `scipy` | Integration, special functions, linear algebra |
| `matplotlib.pyplot` | Visualization |
| `sympy` | Symbolic mathematics |
| `lumapi` | Electromagnetic field calculation |

**Note:** You have to use `lumapi`/Lumerical FDTD to calculate the electromagnetic field. Analytical formulas may guide source/geometry setup and validation, but they cannot replace the FDTD simulation or be used to directly generate final PNG/CSV data.

SHG intensity, phase, far-field vortex profiles, and on-axis interference post-processing may use the equations described in the paper, evaluated on FDTD-exported fields. Do not construct analytical electromagnetic SHG fields to bypass FDTD.

### Style Requirements
| Requirement | Description |
| ------------ | ----------- |
| **Vectorization** | Use NumPy array operations, not `for` loops. |
| **Formatting** | `plt.style.use('seaborn-v0_8-paper')`, LaTeX labels (`r'$\alpha$'`), DPI=300. |
| **Safety** | Add assertions for physical constraints (e.g., `assert energy > 0`). |

---

## 5. Data Files to Reproduce

### FDTD nonlinear plasmonic metasurface simulations
**Files**: `data/fig3c_1.fsp` through `data/fig3c_9.fsp`; `data/fig4c_1.fsp` through `data/fig4c_9.fsp`; exported field monitor CSV/NPY/HDF5 data as needed under `data/`

Known setup from the text/caption:
- Platform: gold  $C_3$  plasmonic metasurfaces fabricated on ITO-coated glass.
- Meta-atom geometry: gold thickness 30 nm; arm length 160 nm; arm width 80 nm; center-to-center meta-atom distance 500 nm.
- Illumination: circularly polarized FW and horizontally polarized FW; use the paper's experimental wavelength information (1064 nm for Fig. 3 and vortex-plate setup, with 1225 nm noted for improved SHG efficiency where applicable). The final electromagnetic fields must come from FDTD.
- q-index mapping for both Fig. 3(c) and Fig. 4(c): `_1`:  $q=-4/3$ ; `_2`:  $q=-1$ ; `_3`:  $q=-2/3$ ; `_4`:  $q=-1/3$ ; `_5`:  $q=0$ ; `_6`:  $q=1/3$ ; `_7`:  $q=2/3$ ; `_8`:  $q=1$ ; `_9`:  $q=4/3$ .
- Required Fig. 3(c) configurations: Gaussian FW with angular momentum state  $(\sigma,0)_\omega$  and horizontal-FW interference cases; SHG target OAM follows  $3\sigma q$ .
- Required Fig. 4(c) configurations: vortex FW generated by a vortex plate with  $m=1/2$ , giving FW states  $(-1,1)_\omega$  and  $(1,-1)_\omega$ , plus horizontal-FW interference cases; SHG target OAM follows  $2l+3\sigma q$ .
- Export complex  $E$  and  $H$  fields, SHG near/far fields, and any monitor data needed to derive the final beam profiles. All target PNG and CSV files must derive from these FDTD fields.

### Figure 3(c): Simulated SHG beam profiles for Gaussian FW
**Files**: `data/fig3c_1.png` through `data/fig3c_9.png`; matching `.csv` files

Reproduce the simulated SHG beam profiles under Gaussian FW excitation for the nine topological charges. Each indexed output should contain the corresponding q case from Fig. 3(c), including the LCP/RCP circular-polarization rows and the horizontal-polarization interference row where applicable. All maps must be derived from FDTD-exported fields.

### Figure 4(c): Simulated SHG beam profiles for vortex FW
**Files**: `data/fig4c_1.png` through `data/fig4c_9.png`; matching `.csv` files

Reproduce the simulated SHG beam profiles under vortex FW excitation for the nine topological charges. Each indexed output should contain the corresponding q case from Fig. 4(c), including the LCP/RCP circular-polarization rows and the horizontal-polarization interference row where applicable. All maps must be derived from FDTD-exported fields.



---

## 6. Banned Practices

| Category | Banned | Allowed Alternative |
| -------- | ------- | ------------------- |
| **Hardcoding** | Pre-calculating or hardcoding results | Implement actual physical equations/algorithms |
| **Shortcuts** | Practical shortcuts that skip FDTD physics | Full `lumapi`/FDTD simulation and field extraction |
| **Cheating** | Hardcoded arrays or analytical electromagnetic fields used as final plot/CSV data | Electromagnetic fields generated only from FDTD monitor data; SHG intensity, phase, far-field vortex profiles, and interference maps derived from those fields using the paper's nonlinear spin-orbit interaction framework |

---

## 7. Validation Requirements

| Metric | Target |
| ------ | ------- |
| **Relative Error** | No fixed relative-error tolerance is specified for this paper unless target panel masks are later provided; generated panels must be non-trivial, physically plausible, and visually consistent with the supplied references. |
| **Table Reproduction** | Not applicable for the requested targets |
| **Figure Reproduction** | Fig. 3(c) and Fig. 4(c) must be generated as q-indexed individual PNG files with matching CSV plotting data directly under `data/`. |

---

## 8. Deliverables

| Deliverable | Path |
| ------------| ----- |
| Implementation Plan | `reproduction/plan.md` |
| Compute Scripts | `reproduction/fig3c_compute.py`, `reproduction/fig4c_compute.py` |
| Simulation Files | `data/fig3c_1.fsp` through `data/fig3c_9.fsp`; `data/fig4c_1.fsp` through `data/fig4c_9.fsp` |
| Final Figures | Per-subfigure files `data/fig3c_1.png` through `data/fig3c_9.png`; `data/fig4c_1.png` through `data/fig4c_9.png` |
| Plotting Data | Matching per-subfigure CSV files directly under `data/` |
| Analysis Document | `reproduction/ANALYSIS.md` |

(End of file)
