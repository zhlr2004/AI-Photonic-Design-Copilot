"""External, immutable example library backed by SQLite and an artifact directory."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Mapping

from .contracts import ContractValidator, canonical_json
from .gates import Approval, require_result_gate


QUALITY_ORDER = {
    "archived": 0,
    "executed": 1,
    "validated": 2,
    "reviewed": 3,
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ExampleLibrary:
    def __init__(self, root: Path, validator: ContractValidator | None = None) -> None:
        self.root = root.expanduser().resolve()
        self.artifacts_root = self.root / "artifacts"
        self.staging_root = self.root / "staging"
        self.database_path = self.root / "examples.sqlite3"
        self.validator = validator or ContractValidator()
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.staging_root.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS examples (
                    example_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    solver TEXT,
                    device_type TEXT,
                    manifest_json TEXT NOT NULL,
                    PRIMARY KEY (example_id, version)
                )
                """
            )

    def stage_candidate(self, candidate: Mapping[str, Any]) -> Path:
        self.validator.validate(candidate, "ExampleCandidate")
        target = self.staging_root / f"{candidate['candidate_id']}.json"
        if target.exists():
            raise FileExistsError(f"candidate already exists: {candidate['candidate_id']}")
        target.write_text(canonical_json(candidate) + "\n", encoding="utf-8")
        return target

    def integrity_checks(self, candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []
        for artifact in candidate["manifest_draft"]["artifacts"]:
            source = Path(artifact["uri"]).expanduser()
            exists = source.is_file()
            checks.append(
                {
                    "name": "artifact_exists",
                    "method": "filesystem",
                    "passed": exists,
                    "threshold": None,
                    "value": str(source),
                    "input_refs": [],
                    "details": {},
                }
            )
            if exists and artifact.get("sha256"):
                actual = file_sha256(source)
                checks.append(
                    {
                        "name": "artifact_hash",
                        "method": "sha256",
                        "passed": actual.lower() == artifact["sha256"].lower(),
                        "threshold": None,
                        "value": actual,
                        "input_refs": [],
                        "details": {},
                    }
                )
        return checks

    def publish(
        self,
        candidate: Mapping[str, Any],
        *,
        validation_report: Mapping[str, Any],
        approval: Approval,
    ) -> dict[str, Any]:
        self.validator.validate(candidate, "ExampleCandidate")
        self.validator.validate(validation_report, "ValidationReport")
        require_result_gate(validation_report, approval)
        checks = self.integrity_checks(candidate)
        if not checks or not all(check["passed"] for check in checks):
            raise ValueError("candidate artifacts failed integrity checks")

        manifest = dict(candidate["manifest_draft"])
        example_id = manifest["example_id"]
        version = manifest["version"]
        destination = self.artifacts_root / example_id / version
        if destination.exists():
            raise FileExistsError(f"immutable example already exists: {example_id}@{version}")
        destination.mkdir(parents=True)

        copied: list[dict[str, Any]] = []
        try:
            for artifact in manifest["artifacts"]:
                source = Path(artifact["uri"]).expanduser().resolve()
                target = destination / source.name
                if target.exists():
                    raise FileExistsError(f"duplicate artifact filename: {source.name}")
                shutil.copy2(source, target)
                copied.append(
                    {
                        **artifact,
                        "uri": str(target),
                        "sha256": file_sha256(target),
                        "size_bytes": target.stat().st_size,
                    }
                )
            manifest["artifacts"] = copied
            manifest["reviewer"] = approval.reviewer
            self.validator.validate(manifest, "ExampleManifest")
            manifest_path = destination / "example-manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO examples (
                        example_id, version, mode, quality, solver, device_type,
                        manifest_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        example_id,
                        version,
                        manifest["mode"],
                        manifest["quality"],
                        manifest.get("solver"),
                        manifest.get("device_type"),
                        canonical_json(manifest),
                    ),
                )
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise
        return manifest

    def get(self, example_id: str, version: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT manifest_json FROM examples WHERE example_id=? AND version=?",
                (example_id, version),
            ).fetchone()
        if row is None:
            raise KeyError(f"{example_id}@{version}")
        return json.loads(row["manifest_json"])

    def search(
        self,
        *,
        mode: str | None = None,
        solver: str | None = None,
        device_type: str | None = None,
        material: str | None = None,
        observable: str | None = None,
        minimum_quality: str = "validated",
        include_failures: bool = False,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[str] = []
        for column, value in (
            ("mode", mode),
            ("solver", solver),
            ("device_type", device_type),
        ):
            if value is not None:
                clauses.append(f"{column}=?")
                parameters.append(value)
        query = "SELECT manifest_json FROM examples"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        minimum = QUALITY_ORDER[minimum_quality]
        results: list[dict[str, Any]] = []
        for row in rows:
            manifest = json.loads(row["manifest_json"])
            if QUALITY_ORDER[manifest["quality"]] < minimum:
                continue
            if material and material not in manifest.get("materials", []):
                continue
            if observable and observable not in manifest.get("observables", []):
                continue
            if not include_failures and "failure" in manifest.get("tags", []):
                continue
            results.append(
                {
                    "example_id": manifest["example_id"],
                    "version": manifest["version"],
                    "quality": manifest["quality"],
                    "similarity_reason": "matched structured filters",
                    "reusable_fields": [
                        "physics.geometry",
                        "physics.materials",
                        "numerics",
                    ],
                    "limitations": (
                        []
                        if manifest["quality"] in {"validated", "reviewed"}
                        else ["not convergence validated"]
                    ),
                }
            )
        return sorted(
            results,
            key=lambda item: (
                -QUALITY_ORDER[item["quality"]],
                item["example_id"],
                item["version"],
            ),
        )
