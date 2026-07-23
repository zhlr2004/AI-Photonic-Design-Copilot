"""Versioned contract validation and stable hashing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker


class ContractValidationError(ValueError):
    """Raised when a document violates its schema or a cross-field rule."""


def canonical_json(document: Mapping[str, Any]) -> str:
    """Return deterministic JSON for hashes and immutable records."""

    return json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_hash(document: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


class ContractValidator:
    """Validate V1 documents against JSON Schema and platform invariants."""

    def __init__(self, schema_path: Path | None = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self.schema_path = schema_path or root / "schemas" / "v1" / "contracts.schema.json"
        self.catalog = json.loads(self.schema_path.read_text(encoding="utf-8"))
        self._format_checker = FormatChecker()

    @property
    def schema_names(self) -> tuple[str, ...]:
        excluded = {
            "SchemaHeader",
            "ArtifactRef",
            "Quantity",
            "Provenance",
            "EvidenceEntry",
            "TargetPanel",
            "Assumption",
            "ValidationCheck",
            "ExampleCatalogEntry",
            "SourceSnapshotFile",
            "CurationItem",
            "ContractDocument",
        }
        return tuple(name for name in self.catalog["$defs"] if name not in excluded)

    def validate(self, document: Mapping[str, Any], schema_name: str | None = None) -> None:
        name = schema_name or str(document.get("schema_id", ""))
        if name not in self.catalog["$defs"]:
            raise ContractValidationError(f"unknown schema_id: {name!r}")

        schema = {
            "$schema": self.catalog["$schema"],
            "$defs": self.catalog["$defs"],
            "$ref": f"#/$defs/{name}",
        }
        validator = Draft202012Validator(schema, format_checker=self._format_checker)
        errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
        if errors:
            rendered = "; ".join(
                f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}"
                for error in errors
            )
            raise ContractValidationError(rendered)

        rule = getattr(self, f"_check_{name}", None)
        if rule is not None:
            rule(document)

    def _check_Evidence(self, document: Mapping[str, Any]) -> None:
        ids = [entry["parameter_id"] for entry in document["entries"]]
        if len(ids) != len(set(ids)):
            raise ContractValidationError("Evidence parameter_id values must be unique")

    def _check_SimulationContract(self, document: Mapping[str, Any]) -> None:
        cases = document["numerics"]["convergence_cases"]
        if not cases:
            raise ContractValidationError("at least one convergence case must be proposed")
        unaccepted = [
            assumption["parameter_id"]
            for assumption in document["assumptions"]
            if not assumption["accepted"]
        ]
        if unaccepted:
            joined = ", ".join(unaccepted)
            raise ContractValidationError(f"material assumptions require acceptance: {joined}")

        requested = set(document["objective"]["observables"])
        raw_or_derived = set(document["outputs"]["raw"]) | set(document["outputs"]["derived"])
        missing = requested - raw_or_derived
        if missing:
            raise ContractValidationError(
                "requested observables missing from outputs: " + ", ".join(sorted(missing))
            )
        resources = document["resources"]
        cpu_cores = resources.get("cpu_cores")
        if cpu_cores is not None and resources["mpi_processes"] > cpu_cores:
            raise ContractValidationError(
                "mpi_processes cannot exceed the declared cpu_cores"
            )

    def _check_ValidationReport(self, document: Mapping[str, Any]) -> None:
        convergence = document["convergence"]
        if document["completion_state"] == "validated":
            if not convergence["performed"]:
                raise ContractValidationError(
                    "validated completion requires performed convergence"
                )
            if not document["passed"]:
                raise ContractValidationError("validated completion requires passed checks")

    def _check_ExampleCandidate(self, document: Mapping[str, Any]) -> None:
        if document["failure_labels"]:
            quality = document["manifest_draft"]["quality"]
            if quality in {"validated", "reviewed"}:
                raise ContractValidationError(
                    "failure-labelled examples cannot be validated or reviewed"
                )
        if document["sensitivity"] != document["manifest_draft"]["sensitivity"]:
            raise ContractValidationError(
                "candidate and manifest sensitivity must be identical"
            )

    def _check_ExampleCatalog(self, document: Mapping[str, Any]) -> None:
        keys = [
            (entry["example_id"], entry["version"]) for entry in document["entries"]
        ]
        if len(keys) != len(set(keys)):
            raise ContractValidationError("catalog entries must be unique")
        if keys != sorted(keys):
            raise ContractValidationError(
                "catalog entries must be sorted by example_id and version"
            )

    def _check_G3ReviewDecision(self, document: Mapping[str, Any]) -> None:
        if document["allow_publication"] and not document["approved"]:
            raise ContractValidationError(
                "publication cannot be allowed by a rejected G3 decision"
            )
