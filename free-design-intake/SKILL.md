---
name: free-design-intake
description: >-
  Converts a human photonic-device objective and constraints into a validated,
  solver-independent SimulationContract. Use for free-design mode before
  selecting Meep, Lumerical, or another solver adapter.
disable-model-invocation: true
---

# Free-design requirement intake

Produce `simulation-contract.json` conforming to:

```text
../schemas/v1/contracts.schema.json#/$defs/SimulationContract
```

## Workflow

1. Read `../fdtd-core/checklists/requirement-intake.md`.
2. Establish device objective, observables, geometry, materials, fabrication
   constraints, sources, boundaries, monitors, accuracy, and resources.
3. Ask only for omissions that materially change physics, cost, or
   interpretation.
4. Query the Example Library using device, material, band, observable,
   dimensionality, mode, and minimum quality.
5. Record every reused example ID/version, quality, reusable field, and
   transformation in `example_references`.
6. Mark example-derived values as suggestions; they never override an explicit
   user constraint.
7. Include independent mesh, PML/padding, and run-control convergence cases.
8. Keep all assumptions visible with reason, consequence, and acceptance.
9. Validate the completed contract. Correct the document rather than weakening
   the schema.

## Gate

Do not select a solver or generate a model until:

- requested observables also appear in raw or derived outputs;
- material models and valid spectral ranges are identified;
- interpretation-changing assumptions are accepted;
- G1 contract review is recorded.
