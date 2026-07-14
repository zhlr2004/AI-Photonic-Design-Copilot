# Convergence and validation

Convergence is measured on the requested observable. A visually smooth field
or an auto-shutoff event is not a convergence test.

## Required plan

Plan independent variations around a declared base case:

1. **Mesh**: increase global mesh accuracy and/or reduce local mesh spacing.
2. **PML and padding**: increase PML layers or change formulation, then increase
   separation between the device/near field and PML.
3. **Run control**: increase simulation-time ceiling and tighten auto shutoff.

Change one family at a time unless using a designed convergence matrix. Include
the planned cases even if the user declines to execute them.

## Comparison metric

Choose a metric before running:

- maximum absolute or relative spectral error;
- normed difference across the requested band;
- shift in resonance wavelength/frequency and Q;
- change in mode amplitude, phase, or integrated power;
- change in a scalar objective or far-field feature.

Use a denominator floor for relative errors near zeros and report both absolute
and relative changes when a spectrum contains nulls. Align axes without silently
extrapolating. Thresholds come from the simulation contract.

`scripts/validate_results.py` can check finite arrays, frequency/wavelength
axes, optional lossless R+T balance, and relative changes between exported
NPZ/JSON/CSV cases. It does not understand `.fsp` physics and cannot replace
model-specific checks.

## Physics checks

Apply only checks whose assumptions hold:

- passive lossless device: total reflected, transmitted, diffracted, and
  radiated power is near incident power;
- reciprocal device: consistently normalized reciprocal S parameters agree;
- guided-wave device: mode-expansion power agrees with total monitor power;
- symmetry reduction: reduced and full-domain results agree for one case;
- far field: integrated projected power agrees with a suitable enclosing power
  measurement;
- resonance: frequency and Q remain stable with mesh and record duration;
- reference geometry: result agrees with an analytic or trusted simple case.

Loss, gain, unmonitored radiation, or omitted modes invalidate a naive
`R + T = 1` requirement.

## Suggested execution order

1. Reduced smoke case.
2. Base case.
3. Mesh refinement cases.
4. PML-layer/formulation cases.
5. Padding cases if reactive or evanescent fields approach PML.
6. Time-ceiling and auto-shutoff cases.
7. Relevant physics checks.
8. One combined tighter case to detect interacting errors.

## Evidence record

For each case save:

- case identifier and changed parameter;
- `.fsp`/script/configuration hash or path;
- solver version and run command;
- runtime, memory if available, and termination reason;
- raw observable and comparison metric;
- warnings and pass/fail against the declared threshold.

## Completion rule

- Not run: **Generated**.
- Base run only or user-declined convergence: at most **Executed**.
- Declared convergence and relevant physics checks pass: **Validated**.

Never convert a default solver setting into an accuracy claim without evidence.
