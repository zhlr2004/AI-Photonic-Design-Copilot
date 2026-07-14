# Versioned contracts

`v1/contracts.schema.json` is the machine-readable boundary between workflow
tools, solver adapters, validation, and the external example library.

Use a definition directly with a JSON Pointer, for example:

```text
schemas/v1/contracts.schema.json#/$defs/SimulationContract
schemas/v1/contracts.schema.json#/$defs/ValidationReport
```

The catalog defines:

- `WorkflowRequest`, `PaperManifest`, `Evidence`, and `Targets`;
- `SimulationContract`;
- `ToolManifest`, `SolverCapability`, and `ToolCallRecord`;
- `RunManifest` and `ValidationReport`;
- `ExampleManifest`, `ExampleCandidate`, and `ExperienceRecord`.

## Compatibility rules

- `schema_version` is `1.0` for every V1 document.
- Completion states are lowercase: `generated`, `executed`, `validated`.
- Evidence never silently promotes an assumption to a paper-specified value.
- Every simulation contract includes proposed convergence cases, even when the
  user later chooses a base-only run.
- Solver adapters return `unsupported`, `requires_assumption`, or
  `requires_manual_implementation` rather than silently dropping requirements.
- Published example versions are immutable.

Validate documents through `photonic_copilot.contracts.ContractValidator` or
directly with a JSON Schema Draft 2020-12 implementation.
