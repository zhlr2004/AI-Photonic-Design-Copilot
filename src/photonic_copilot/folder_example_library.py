"""Portable, immutable folder-backed example library."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping

from .contracts import ContractValidator, canonical_hash, canonical_json
from .gates import Approval, require_result_gate


QUALITY_ORDER = {
    "archived": 0,
    "executed": 1,
    "validated": 2,
    "reviewed": 3,
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DOCUMENT_FIELDS = {
    "paper_manifest": "paper-manifest.json",
    "evidence": "evidence.json",
    "targets": "targets.json",
    "simulation_contract": "simulation-contract.json",
    "run_manifest": "run-manifest.json",
    "validation_report": "validation-report.json",
}
DOCUMENT_SCHEMAS = {
    "paper_manifest": "PaperManifest",
    "evidence": "Evidence",
    "targets": "Targets",
    "simulation_contract": "SimulationContract",
    "run_manifest": "RunManifest",
    "validation_report": "ValidationReport",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_id(value: str, label: str) -> None:
    if not SAFE_ID.fullmatch(value) or value in {".", ".."}:
        raise ValueError(f"unsafe {label}: {value!r}")


def _reject_symlink(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"symbolic links are not allowed: {path}")


def _walk_files(root: Path) -> list[Path]:
    _reject_symlink(root)
    if root.is_file():
        return [root]
    if not root.is_dir():
        raise FileNotFoundError(root)
    files: list[Path] = []
    casefolded: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        _reject_symlink(path)
        relative = path.relative_to(root).as_posix()
        folded = relative.casefold()
        previous = casefolded.get(folded)
        if previous is not None and previous != relative:
            raise ValueError(
                f"case-insensitive path collision: {previous!r} and {relative!r}"
            )
        casefolded[folded] = relative
        if path.is_file():
            files.append(path)
    return files


def tree_snapshot(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    entries: list[dict[str, Any]] = []
    total_size = 0
    if root.is_file():
        entries.append(
            {
                "path": root.name,
                "size_bytes": root.stat().st_size,
                "sha256": file_sha256(root),
            }
        )
        total_size = root.stat().st_size
    else:
        for path in _walk_files(root):
            size = path.stat().st_size
            total_size += size
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "size_bytes": size,
                    "sha256": file_sha256(path),
                }
            )
    fingerprint = hashlib.sha256(canonical_json({"files": entries}).encode()).hexdigest()
    return {
        "schema_id": "SourceSnapshot",
        "schema_version": "1.0",
        "source_uri": str(root),
        "captured_at": utc_now(),
        "tree_sha256": fingerprint,
        "size_bytes": total_size,
        "files": entries,
    }


def tree_sha256(root: Path) -> tuple[str, int]:
    snapshot = tree_snapshot(root)
    return str(snapshot["tree_sha256"]), int(snapshot["size_bytes"])


def _copy_entry(source: Path, target: Path) -> None:
    _reject_symlink(source)
    if source.is_dir():
        _walk_files(source)
        shutil.copytree(source, target, symlinks=False)
    elif source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    else:
        raise FileNotFoundError(source)


def _safe_relative_uri(value: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe relative URI: {value!r}")
    return path


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


class FolderExampleLibrary:
    """Self-contained examples with a rebuildable JSON catalog."""

    def __init__(
        self,
        root: Path | None = None,
        validator: ContractValidator | None = None,
        *,
        project_root: Path | None = None,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        configured = os.environ.get("PHOTONIC_EXAMPLE_LIBRARY_ROOT")
        self.root = (
            root
            or (Path(configured) if configured else None)
            or (project_root or repository_root) / "example-library"
        ).expanduser().resolve()
        self.examples_root = self.root / "examples"
        self.staging_root = self.root / "staging"
        self.locks_root = self.root / ".locks"
        self.catalog_path = self.root / "catalog.json"
        self.validator = validator or ContractValidator()

        if (self.root / "examples.sqlite3").exists() and not self.catalog_path.exists():
            raise RuntimeError(
                "legacy SQLite example library detected; stage a read-only migration "
                "before initializing the folder catalog"
            )
        self.examples_root.mkdir(parents=True, exist_ok=True)
        self.staging_root.mkdir(parents=True, exist_ok=True)
        self.locks_root.mkdir(parents=True, exist_ok=True)
        if not self.catalog_path.exists():
            self._write_catalog([])

    @contextmanager
    def _catalog_lock(self) -> Iterator[None]:
        lock = self.locks_root / "catalog.lock"
        descriptor: int | None = None
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, f"{os.getpid()}\n".encode())
            yield
        except FileExistsError as exc:
            raise RuntimeError("example catalog is locked by another publisher") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
                lock.unlink(missing_ok=True)

    def _empty_catalog(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "schema_id": "ExampleCatalog",
            "schema_version": "1.0",
            "format_version": 1,
            "updated_at": utc_now(),
            "entries": sorted(
                entries, key=lambda item: (item["example_id"], item["version"])
            ),
        }

    def _write_catalog(self, entries: list[dict[str, Any]]) -> None:
        catalog = self._empty_catalog(entries)
        self.validator.validate(catalog, "ExampleCatalog")
        _atomic_json(self.catalog_path, catalog)

    def _read_catalog(self) -> dict[str, Any]:
        try:
            catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
            self.validator.validate(catalog, "ExampleCatalog")
            return catalog
        except Exception as exc:
            raise RuntimeError(
                "catalog.json is missing or invalid; run rebuild_catalog()"
            ) from exc

    def _copy_document(
        self,
        manifest: dict[str, Any],
        field: str,
        documents_dir: Path,
    ) -> None:
        value = manifest.get(field)
        if value is None:
            return
        source = Path(value).expanduser().resolve()
        target = documents_dir / DOCUMENT_FIELDS[field]
        _copy_entry(source, target)
        manifest[field] = target.relative_to(documents_dir.parent.parent).as_posix()

    def stage_candidate(
        self,
        candidate: Mapping[str, Any],
        *,
        source_snapshot: Mapping[str, Any] | None = None,
    ) -> Path:
        self.validator.validate(candidate, "ExampleCandidate")
        candidate_id = str(candidate["candidate_id"])
        _validate_id(candidate_id, "candidate_id")
        destination = self.staging_root / candidate_id
        if destination.exists():
            raise FileExistsError(f"candidate already exists: {candidate_id}")

        temporary = self.staging_root / f".staging-{candidate_id}-{uuid.uuid4().hex}"
        payload = temporary / "payload"
        documents = payload / "documents"
        artifacts = payload / "artifacts"
        documents.mkdir(parents=True)
        artifacts.mkdir(parents=True)
        staged = json.loads(json.dumps(candidate))
        manifest = staged["manifest_draft"]
        try:
            for field in DOCUMENT_FIELDS:
                self._copy_document(manifest, field, documents)

            used_names: set[str] = set()
            copied_artifacts: list[dict[str, Any]] = []
            for index, artifact in enumerate(manifest["artifacts"]):
                source = Path(artifact["uri"]).expanduser().resolve()
                name = source.name or f"artifact-{index}"
                folded = name.casefold()
                if folded in used_names:
                    raise ValueError(f"duplicate artifact target name: {name}")
                used_names.add(folded)
                target = artifacts / name
                _copy_entry(source, target)
                digest, size = (
                    (file_sha256(target), target.stat().st_size)
                    if target.is_file()
                    else tree_sha256(target)
                )
                copied_artifacts.append(
                    {
                        **artifact,
                        "uri": target.relative_to(temporary).as_posix(),
                        "sha256": digest,
                        "size_bytes": size,
                    }
                )
            manifest["artifacts"] = copied_artifacts
            self.validator.validate(staged, "ExampleCandidate")
            _atomic_json(temporary / "example-candidate.json", staged)
            if source_snapshot is not None:
                self.validator.validate(source_snapshot, "SourceSnapshot")
                _atomic_json(temporary / "source-snapshot.json", source_snapshot)
            _atomic_json(
                temporary / "staging-record.json",
                {
                    "candidate_id": candidate_id,
                    "created_at": utc_now(),
                    "candidate_sha256": canonical_hash(staged),
                    "source_snapshot_sha256": (
                        source_snapshot.get("tree_sha256")
                        if source_snapshot is not None
                        else None
                    ),
                },
            )
            os.replace(temporary, destination)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return destination

    def _load_staged(self, candidate_id: str) -> tuple[Path, dict[str, Any]]:
        _validate_id(candidate_id, "candidate_id")
        directory = self.staging_root / candidate_id
        candidate_path = directory / "example-candidate.json"
        if not candidate_path.is_file():
            raise FileNotFoundError(candidate_path)
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        self.validator.validate(candidate, "ExampleCandidate")
        return directory, candidate

    def integrity_checks(self, candidate_id: str) -> list[dict[str, Any]]:
        directory, candidate = self._load_staged(candidate_id)
        checks: list[dict[str, Any]] = []
        manifest = candidate["manifest_draft"]
        references = [
            value for field in DOCUMENT_FIELDS if (value := manifest.get(field))
        ]
        references.extend(item["uri"] for item in manifest["artifacts"])
        for uri in references:
            relative = _safe_relative_uri(str(uri))
            path = directory.joinpath(*relative.parts).resolve()
            try:
                path.relative_to(directory.resolve())
                inside = True
            except ValueError:
                inside = False
            exists = inside and (path.is_file() or path.is_dir()) and not path.is_symlink()
            checks.append(
                {
                    "name": "staged_reference",
                    "method": "filesystem",
                    "passed": exists,
                    "threshold": None,
                    "value": str(uri),
                    "input_refs": [],
                    "details": {"inside_staging": inside},
                }
            )
        for artifact in manifest["artifacts"]:
            relative = _safe_relative_uri(artifact["uri"])
            path = directory.joinpath(*relative.parts)
            if not path.exists():
                continue
            digest, _ = (
                (file_sha256(path), path.stat().st_size)
                if path.is_file()
                else tree_sha256(path)
            )
            checks.append(
                {
                    "name": "artifact_hash",
                    "method": "sha256",
                    "passed": digest.lower() == artifact["sha256"].lower(),
                    "threshold": None,
                    "value": digest,
                    "input_refs": [],
                    "details": {"uri": artifact["uri"]},
                }
            )
        for field, schema_name in DOCUMENT_SCHEMAS.items():
            uri = manifest.get(field)
            if uri is None:
                continue
            relative = _safe_relative_uri(uri)
            path = directory.joinpath(*relative.parts)
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
                self.validator.validate(document, schema_name)
                passed, details = True, {}
            except Exception as exc:
                passed, details = False, {"error": str(exc)}
            checks.append(
                {
                    "name": f"{field}_schema",
                    "method": "json_schema",
                    "passed": passed,
                    "threshold": None,
                    "value": uri,
                    "input_refs": [],
                    "details": details,
                }
            )
        return checks

    def _catalog_entry(
        self, manifest: Mapping[str, Any], manifest_path: Path
    ) -> dict[str, Any]:
        return {
            "example_id": manifest["example_id"],
            "version": manifest["version"],
            "manifest_uri": manifest_path.relative_to(self.root).as_posix(),
            "manifest_sha256": file_sha256(manifest_path),
            "mode": manifest["mode"],
            "quality": manifest["quality"],
            "solver": manifest.get("solver"),
            "device_type": manifest.get("device_type"),
            "materials": manifest.get("materials", []),
            "observables": manifest.get("observables", []),
            "tags": manifest.get("tags", []),
            "sensitivity": manifest["sensitivity"],
        }

    def publish(
        self,
        candidate: Mapping[str, Any] | str,
        *,
        validation_report: Mapping[str, Any] | None,
        approval: Approval,
    ) -> dict[str, Any]:
        candidate_id = (
            candidate if isinstance(candidate, str) else str(candidate["candidate_id"])
        )
        staging_dir, staged = self._load_staged(candidate_id)
        quality = staged["manifest_draft"]["quality"]
        if validation_report is not None:
            self.validator.validate(validation_report, "ValidationReport")
            require_result_gate(validation_report, approval)
        elif quality != "archived":
            raise ValueError(
                "only archived examples may be published without ValidationReport"
            )
        elif approval.gate != "G3" or not approval.approved:
            raise ValueError("G3 approval is required for archived publication")
        checks = self.integrity_checks(candidate_id)
        if not checks or not all(item["passed"] for item in checks):
            raise ValueError("candidate failed staged integrity checks")
        if not staged.get("license_check") or not staged["license_check"].get("passed"):
            raise ValueError("license check must pass before publication")
        if staged["sensitivity"] != staged["manifest_draft"]["sensitivity"]:
            raise ValueError("candidate and manifest sensitivity differ")

        manifest = json.loads(json.dumps(staged["manifest_draft"]))
        quality = manifest["quality"]
        if quality in {"validated", "reviewed"} and (
            validation_report is None
            or validation_report["completion_state"] != "validated"
            or not validation_report["passed"]
        ):
            raise ValueError("validated/reviewed examples require validated results")
        if staged["failure_labels"]:
            if quality not in {"archived", "executed"}:
                raise ValueError("failure cases can only be archived or executed")
            if "failure" not in manifest.get("tags", []):
                raise ValueError("failure cases require the failure tag")

        snapshot_hash = canonical_hash(staged)
        approved_hash = approval.details.get("candidate_sha256")
        if approved_hash != snapshot_hash:
            raise ValueError("G3 approval is not bound to the staged candidate hash")

        example_id = str(manifest["example_id"])
        version = str(manifest["version"])
        _validate_id(example_id, "example_id")
        _validate_id(version, "version")
        final_dir = self.examples_root / example_id / version
        if final_dir.exists():
            raise FileExistsError(f"immutable example already exists: {example_id}@{version}")
        parent = final_dir.parent
        parent.mkdir(parents=True, exist_ok=True)
        temporary = parent / f".publishing-{version}-{uuid.uuid4().hex}"
        try:
            shutil.copytree(staging_dir / "payload" / "documents", temporary / "documents")
            shutil.copytree(staging_dir / "payload" / "artifacts", temporary / "artifacts")
            for field, filename in DOCUMENT_FIELDS.items():
                if manifest.get(field) is not None:
                    manifest[field] = f"documents/{filename}"
            rewritten_artifacts: list[dict[str, Any]] = []
            for artifact in manifest["artifacts"]:
                staged_uri = _safe_relative_uri(artifact["uri"])
                if staged_uri.parts[:2] != ("payload", "artifacts"):
                    raise ValueError(
                        f"artifact is outside payload/artifacts: {artifact['uri']}"
                    )
                artifact_relative = PurePosixPath(*staged_uri.parts[2:])
                target = temporary.joinpath("artifacts", *artifact_relative.parts)
                digest, size = (
                    (file_sha256(target), target.stat().st_size)
                    if target.is_file()
                    else tree_sha256(target)
                )
                rewritten_artifacts.append(
                    {
                        **artifact,
                        "uri": PurePosixPath("artifacts", artifact_relative).as_posix(),
                        "sha256": digest,
                        "size_bytes": size,
                    }
                )
            manifest["artifacts"] = rewritten_artifacts
            manifest["reviewer"] = approval.reviewer
            self.validator.validate(manifest, "ExampleManifest")
            manifest_path = temporary / "example-manifest.json"
            _atomic_json(manifest_path, manifest)
            os.replace(temporary, final_dir)

            with self._catalog_lock():
                catalog = self._read_catalog()
                entry = self._catalog_entry(
                    manifest, final_dir / "example-manifest.json"
                )
                entries = list(catalog["entries"])
                entries.append(entry)
                self._write_catalog(entries)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            if final_dir.exists() and not (final_dir / "example-manifest.json").exists():
                shutil.rmtree(final_dir, ignore_errors=True)
            raise
        return manifest

    def publish_reviewed(
        self,
        candidate_id: str,
        *,
        decision: Mapping[str, Any],
        validation_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Publish an already reviewed staging candidate after binding G3."""

        self.validator.validate(decision, "G3ReviewDecision")
        staging_dir, candidate = self._load_staged(candidate_id)
        candidate_hash = canonical_hash(candidate)
        if decision["candidate_id"] != candidate_id:
            raise ValueError("G3 decision candidate_id does not match staging")
        if decision["candidate_sha256"] != candidate_hash:
            raise ValueError("G3 decision does not match the staged candidate hash")
        if not decision["approved"] or not decision["allow_publication"]:
            raise ValueError("G3 decision does not permit publication")
        if decision["approved_quality"] != candidate["manifest_draft"]["quality"]:
            raise ValueError("G3 approved quality differs from candidate quality")

        if validation_report is None:
            validation_uri = candidate["manifest_draft"].get("validation_report")
            if validation_uri is not None:
                relative = _safe_relative_uri(validation_uri)
                validation_path = staging_dir.joinpath(*relative.parts)
                validation_report = json.loads(
                    validation_path.read_text(encoding="utf-8")
                )

        decision_path = staging_dir / "payload" / "documents" / "g3-review-decision.json"
        _atomic_json(decision_path, decision)
        approval = Approval(
            gate="G3",
            approved=True,
            reviewer=str(decision["reviewer"]),
            rationale=str(decision["rationale"]),
            details={"candidate_sha256": candidate_hash},
        )
        return self.publish(
            candidate_id,
            validation_report=validation_report,
            approval=approval,
        )

    def get(self, example_id: str, version: str) -> dict[str, Any]:
        catalog = self._read_catalog()
        for entry in catalog["entries"]:
            if entry["example_id"] == example_id and entry["version"] == version:
                relative = _safe_relative_uri(entry["manifest_uri"])
                path = self.root.joinpath(*relative.parts)
                if file_sha256(path) != entry["manifest_sha256"]:
                    raise ValueError(f"manifest hash mismatch: {example_id}@{version}")
                manifest = json.loads(path.read_text(encoding="utf-8"))
                self.validator.validate(manifest, "ExampleManifest")
                return manifest
        raise KeyError(f"{example_id}@{version}")

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
        minimum = QUALITY_ORDER[minimum_quality]
        results: list[dict[str, Any]] = []
        for entry in self._read_catalog()["entries"]:
            if QUALITY_ORDER[entry["quality"]] < minimum:
                continue
            if mode and entry["mode"] != mode:
                continue
            if solver and entry.get("solver") != solver:
                continue
            if device_type and entry.get("device_type") != device_type:
                continue
            if material and material not in entry.get("materials", []):
                continue
            if observable and observable not in entry.get("observables", []):
                continue
            if not include_failures and "failure" in entry.get("tags", []):
                continue
            results.append(
                {
                    "example_id": entry["example_id"],
                    "version": entry["version"],
                    "quality": entry["quality"],
                    "similarity_reason": "matched structured filters",
                    "reusable_fields": [
                        "physics.geometry",
                        "physics.materials",
                        "numerics",
                    ],
                    "limitations": (
                        []
                        if entry["quality"] in {"validated", "reviewed"}
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

    def rebuild_catalog(self) -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        for path in sorted(self.examples_root.glob("*/*/example-manifest.json")):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self.validator.validate(manifest, "ExampleManifest")
            entries.append(self._catalog_entry(manifest, path))
        with self._catalog_lock():
            self._write_catalog(entries)
        return self._read_catalog()

    def verify_library(self) -> list[str]:
        issues: list[str] = []
        try:
            catalog = self._read_catalog()
        except Exception as exc:
            return [str(exc)]
        for entry in catalog["entries"]:
            try:
                manifest = self.get(entry["example_id"], entry["version"])
                version_dir = self.root / PurePosixPath(entry["manifest_uri"]).parent
                for artifact in manifest["artifacts"]:
                    relative = _safe_relative_uri(artifact["uri"])
                    path = version_dir.joinpath(*relative.parts)
                    digest, _ = (
                        (file_sha256(path), path.stat().st_size)
                        if path.is_file()
                        else tree_sha256(path)
                    )
                    if digest != artifact.get("sha256"):
                        issues.append(f"artifact hash mismatch: {path}")
            except Exception as exc:
                issues.append(
                    f"{entry['example_id']}@{entry['version']}: {exc}"
                )
        return issues

    def stage_legacy_folder(
        self,
        source: Path,
        *,
        candidate_id: str,
    ) -> Path:
        """Copy an untrusted legacy folder for curation without publishing it."""

        _validate_id(candidate_id, "candidate_id")
        source = source.expanduser().resolve()
        snapshot = tree_snapshot(source)
        destination = self.staging_root / candidate_id
        if destination.exists():
            raise FileExistsError(destination)
        temporary = self.staging_root / f".legacy-{candidate_id}-{uuid.uuid4().hex}"
        try:
            _copy_entry(source, temporary / "payload" / "legacy-source")
            _atomic_json(temporary / "source-snapshot.json", snapshot)
            _atomic_json(
                temporary / "staging-record.json",
                {
                    "candidate_id": candidate_id,
                    "source_kind": "legacy_folder",
                    "created_at": utc_now(),
                    "source_snapshot_sha256": snapshot["tree_sha256"],
                    "status": "requires_curation",
                },
            )
            os.replace(temporary, destination)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return destination

    def stage_legacy_sqlite_example(
        self,
        legacy_root: Path,
        *,
        example_id: str,
        version: str,
        candidate_id: str,
    ) -> Path:
        """Copy one legacy SQLite record to staging; never publish it directly."""

        legacy_root = legacy_root.expanduser().resolve()
        legacy = LegacySQLiteExampleLibrary(legacy_root)
        manifest = legacy.get(example_id, version)
        manifest = json.loads(json.dumps(manifest))
        manifest["quality"] = "archived"
        tags = list(manifest.get("tags", []))
        if "legacy-import" not in tags:
            tags.append("legacy-import")
        manifest["tags"] = tags
        for field in DOCUMENT_FIELDS:
            value = manifest.get(field)
            if value is not None and not Path(value).is_absolute():
                manifest[field] = str(legacy_root / value)
        for artifact in manifest.get("artifacts", []):
            if not Path(artifact["uri"]).is_absolute():
                artifact["uri"] = str(legacy_root / artifact["uri"])
        snapshot = tree_snapshot(legacy_root)
        candidate = {
            "schema_id": "ExampleCandidate",
            "schema_version": "1.0",
            "candidate_id": candidate_id,
            "source_kind": "legacy_folder",
            "source_ref": str(legacy_root),
            "source_run_id": None,
            "source_snapshot_sha256": snapshot["tree_sha256"],
            "status": "pending_integrity",
            "manifest_draft": manifest,
            "integrity_checks": [],
            "license_check": {
                "passed": False,
                "notes": "legacy SQLite import requires license review",
            },
            "sensitivity": manifest["sensitivity"],
            "failure_labels": [],
            "submitted_at": utc_now(),
            "submitted_by": "legacy-sqlite-import",
        }
        try:
            return self.stage_candidate(candidate, source_snapshot=snapshot)
        except Exception:
            # A genuinely old record may not satisfy the current manifest schema.
            # Preserve it verbatim in staging so the curator can map it manually.
            destination = self.stage_legacy_folder(
                legacy_root, candidate_id=candidate_id
            )
            _atomic_json(destination / "legacy-record.json", manifest)
            return destination


class LegacySQLiteExampleLibrary:
    """Read-only compatibility view for pre-folder example libraries."""

    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self.database_path = self.root / "examples.sqlite3"
        if not self.database_path.is_file():
            raise FileNotFoundError(self.database_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            f"file:{self.database_path.as_posix()}?mode=ro", uri=True
        )
        connection.row_factory = sqlite3.Row
        return connection

    def get(self, example_id: str, version: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT manifest_json FROM examples WHERE example_id=? AND version=?",
                (example_id, version),
            ).fetchone()
        if row is None:
            raise KeyError(f"{example_id}@{version}")
        return json.loads(row["manifest_json"])

    def search(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT example_id, version, quality FROM examples "
                "ORDER BY example_id, version"
            ).fetchall()
        return [dict(row) for row in rows]
