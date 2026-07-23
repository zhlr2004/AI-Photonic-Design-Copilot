"""Read-only inspection and staging-only normalization of legacy cases."""

from __future__ import annotations

import json
import mimetypes
import re
import shutil
from pathlib import Path
from typing import Any, Mapping

from .contracts import ContractValidator, canonical_hash
from .folder_example_library import (
    DOCUMENT_FIELDS,
    DOCUMENT_SCHEMAS,
    FolderExampleLibrary,
    file_sha256,
    tree_sha256,
    tree_snapshot,
    utc_now,
)


EXCLUDED_PARTS = {
    ".git",
    ".svn",
    ".hg",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".swp", ".tmp", ".bak", ".dmp"}
ALLOWED_SUFFIXES = {
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".lsf",
    ".fsp",
    ".npz",
    ".csv",
    ".h5",
    ".hdf5",
    ".mat",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".pdf",
    ".md",
    ".txt",
    ".log",
}
DOCUMENT_NAMES = {value: key for key, value in DOCUMENT_FIELDS.items()}
DOCUMENT_ALIASES = {
    "contract.json": "simulation_contract",
    "simulation_contract.json": "simulation_contract",
    "run_manifest.json": "run_manifest",
    "validation_report.json": "validation_report",
    "paper_manifest.json": "paper_manifest",
}
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "api_key": re.compile(
        r"(?i)(?:api[_-]?key|token|password|secret)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{12,}"
    ),
    "license_credential": re.compile(
        r"(?i)(?:license[_-]?server|lm_license_file)\s*[:=]\s*\S+"
    ),
}
ABSOLUTE_PATH_PATTERNS = {
    "windows_user_path": re.compile(r"(?i)[A-Z]:\\Users\\[^\\\s]+\\"),
    "posix_user_path": re.compile(r"/(?:home|Users)/[^/\s]+/"),
}


def _read_text(path: Path, limit: int = 2_000_000) -> str | None:
    if path.stat().st_size > limit:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def scan_sensitive(root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            findings.append(
                {"path": str(path), "kind": "symlink", "severity": "blocked"}
            )
            continue
        if not path.is_file():
            continue
        text = _read_text(path)
        if text is None:
            continue
        for name, pattern in {**SECRET_PATTERNS, **ABSOLUTE_PATH_PATTERNS}.items():
            if pattern.search(text):
                findings.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "kind": name,
                        "severity": "blocked",
                    }
                )
    return {"passed": not findings, "findings": findings}


def inspect_case(
    source: Path,
    *,
    candidate_id: str,
    mode: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = source.expanduser().resolve()
    snapshot = tree_snapshot(source)
    items: list[dict[str, Any]] = []
    blocked = False
    required_questions: list[str] = []

    for entry in snapshot["files"]:
        relative = Path(entry["path"])
        parts = set(relative.parts)
        suffix = relative.suffix.lower()
        if parts & EXCLUDED_PARTS or suffix in EXCLUDED_SUFFIXES:
            action, reason = "exclude", "cache, build, VCS, or temporary content"
        elif suffix not in ALLOWED_SUFFIXES:
            action, reason = "needs_human_input", "unrecognized file type"
            required_questions.append(f"Should {entry['path']} be included?")
        else:
            action, reason = "include", "allowed case artifact"
        items.append(
            {
                "path": entry["path"],
                "action": action,
                "reason": reason,
                "source_sha256": entry["sha256"],
                "target_path": None,
                "target_sha256": None,
            }
        )

    sensitive = scan_sensitive(source)
    for finding in sensitive["findings"]:
        blocked = True
        items.append(
            {
                "path": finding["path"],
                "action": "blocked",
                "reason": finding["kind"],
                "source_sha256": None,
                "target_path": None,
                "target_sha256": None,
            }
        )
    report = {
        "schema_id": "ExampleCurationReport",
        "schema_version": "1.0",
        "candidate_id": candidate_id,
        "source_snapshot_sha256": snapshot["tree_sha256"],
        "source_unchanged": True,
        "items": items,
        "added_fields": [],
        "removed_fields": [],
        "unmapped_metadata": [],
        "required_questions": sorted(set(required_questions)),
        "blocked": blocked,
        "recommended_quality": "archived",
    }
    ContractValidator().validate(snapshot, "SourceSnapshot")
    ContractValidator().validate(report, "ExampleCurationReport")
    return snapshot, report


def _category(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".py", ".lsf", ".fsp", ".yaml", ".yml"}:
        return "model"
    if suffix in {".npz", ".h5", ".hdf5", ".mat"}:
        return "raw"
    if suffix in {".csv", ".json"}:
        return "derived"
    if suffix in {".png", ".jpg", ".jpeg", ".svg"}:
        return "plots"
    if suffix in {".log", ".txt"}:
        return "logs"
    return "reports"


def _load_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("metadata must be a JSON object")
    return payload


def prepare_case(
    source: Path,
    *,
    library: FolderExampleLibrary,
    candidate_id: str,
    mode: str,
    target_version: str,
    plan: Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    source = source.expanduser().resolve()
    before = tree_snapshot(source)
    if before["tree_sha256"] != plan["source_snapshot_sha256"]:
        raise ValueError("source changed after inspection; inspect again")
    if plan["blocked"]:
        raise ValueError("cleaning plan contains security blockers")

    staging = library.stage_legacy_folder(source, candidate_id=candidate_id)
    legacy = staging / "payload" / "legacy-source"
    documents = staging / "payload" / "documents"
    artifacts = staging / "payload" / "artifacts"
    documents.mkdir()
    artifacts.mkdir()
    metadata = dict(metadata or {})
    plan_by_path = {
        item["path"]: item for item in plan["items"] if item["source_sha256"]
    }
    copied_artifacts: list[dict[str, Any]] = []
    document_refs: dict[str, str | None] = {field: None for field in DOCUMENT_FIELDS}
    report = json.loads(json.dumps(plan))
    report_by_path = {
        item["path"]: item for item in report["items"] if item["source_sha256"]
    }
    document_invalid = False

    for path in sorted(legacy.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(legacy).as_posix()
        decision = plan_by_path.get(relative)
        if decision is None or decision["action"] == "exclude":
            continue
        if decision["action"] in {"blocked", "needs_human_input"}:
            continue
        field = DOCUMENT_NAMES.get(path.name) or DOCUMENT_ALIASES.get(path.name)
        if field and document_refs[field] is None:
            target = documents / DOCUMENT_FIELDS[field]
            shutil.copy2(path, target)
            try:
                document = json.loads(target.read_text(encoding="utf-8"))
                schema_name = DOCUMENT_SCHEMAS[field]
                allowed = set(
                    ContractValidator().catalog["$defs"][schema_name][
                        "properties"
                    ]
                )
                for key in sorted(set(document) - allowed):
                    report["removed_fields"].append(
                        {
                            "document": target.name,
                            "field": key,
                            "reason": "not allowed by the V1 top-level schema",
                        }
                    )
                    del document[key]
                for key, value in (
                    ("schema_id", schema_name),
                    ("schema_version", "1.0"),
                ):
                    if key not in document:
                        document[key] = value
                        report["added_fields"].append(
                            {
                                "document": target.name,
                                "field": key,
                                "value": value,
                                "source": "curation-tool schema mapping",
                            }
                        )
                target.write_text(
                    json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                try:
                    ContractValidator().validate(document, schema_name)
                except Exception as exc:
                    document_invalid = True
                    report["required_questions"].append(
                        f"{target.name} requires schema repair: {exc}"
                    )
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                document_invalid = True
                report["required_questions"].append(
                    f"{target.name} is not valid JSON: {exc}"
                )
            document_refs[field] = target.relative_to(staging).as_posix()
        else:
            target = artifacts / _category(path) / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            artifact = {
                "uri": target.relative_to(staging).as_posix(),
                "kind": "file",
                "sha256": file_sha256(target),
                "size_bytes": target.stat().st_size,
                "label": relative,
            }
            mime_type = mimetypes.guess_type(target.name)[0]
            if mime_type is not None:
                artifact["mime_type"] = mime_type
            copied_artifacts.append(artifact)
        report_by_path[relative]["target_path"] = target.relative_to(staging).as_posix()
        report_by_path[relative]["target_sha256"] = file_sha256(target)

    shutil.rmtree(legacy)
    after = tree_snapshot(source)
    source_unchanged = before["tree_sha256"] == after["tree_sha256"]
    report["source_unchanged"] = source_unchanged
    quality = metadata.get("quality", "archived")
    if (
        not document_refs["run_manifest"]
        or not document_refs["validation_report"]
        or document_invalid
    ):
        quality = "archived"
        report["required_questions"].append(
            "RunManifest/ValidationReport missing; candidate is limited to archived."
        )
    manifest = {
        "schema_id": "ExampleManifest",
        "schema_version": "1.0",
        "example_id": metadata.get("example_id", candidate_id),
        "version": target_version,
        "mode": mode,
        "quality": quality,
        **document_refs,
        "artifacts": copied_artifacts,
        "device_type": metadata.get("device_type"),
        "materials": metadata.get("materials", []),
        "observables": metadata.get("observables", []),
        "solver": metadata.get("solver"),
        "tags": metadata.get("tags", []),
        "reviewer": None,
        "parent_example": metadata.get("parent_example"),
        "license": metadata.get("license"),
        "sensitivity": metadata.get("sensitivity", "internal"),
    }
    candidate = {
        "schema_id": "ExampleCandidate",
        "schema_version": "1.0",
        "candidate_id": candidate_id,
        "source_kind": "legacy_folder",
        "source_ref": str(source),
        "source_run_id": None,
        "source_snapshot_sha256": before["tree_sha256"],
        "status": "pending_review",
        "manifest_draft": manifest,
        "integrity_checks": [],
        "license_check": metadata.get(
            "license_check",
            {"passed": False, "notes": "requires human license review"},
        ),
        "sensitivity": manifest["sensitivity"],
        "failure_labels": metadata.get("failure_labels", []),
        "submitted_at": utc_now(),
        "submitted_by": metadata.get("submitted_by", "curation-tool"),
    }
    validator = ContractValidator()
    validator.validate(candidate, "ExampleCandidate")
    report["recommended_quality"] = quality
    validator.validate(report, "ExampleCurationReport")
    (staging / "example-candidate.json").write_text(
        json.dumps(candidate, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (staging / "cleaning-plan.json").write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (staging / "cleaning-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    sensitivity = scan_sensitive(staging / "payload")
    (staging / "sensitivity-report.json").write_text(
        json.dumps(sensitivity, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (staging / "g3-review.md").write_text(
        "# G3 review\n\n"
        f"- Candidate: `{candidate_id}`\n"
        f"- Source snapshot: `{before['tree_sha256']}`\n"
        f"- Candidate SHA-256: `{canonical_hash(candidate)}`\n"
        f"- Source unchanged: `{source_unchanged}`\n"
        f"- Recommended quality: `{quality}`\n"
        f"- Sensitive scan passed: `{sensitivity['passed']}`\n"
        "- Decision: pending\n",
        encoding="utf-8",
    )
    if not source_unchanged:
        raise RuntimeError("source case changed during preparation")
    return staging


def load_metadata(path: Path | None) -> dict[str, Any]:
    return _load_metadata(path)


def validate_candidate_directory(directory: Path) -> dict[str, Any]:
    directory = directory.expanduser().resolve()
    candidate = json.loads(
        (directory / "example-candidate.json").read_text(encoding="utf-8")
    )
    validator = ContractValidator()
    validator.validate(candidate, "ExampleCandidate")
    issues: list[str] = []
    for artifact in candidate["manifest_draft"]["artifacts"]:
        path = directory / artifact["uri"]
        if not path.is_file():
            issues.append(f"missing artifact: {artifact['uri']}")
        elif file_sha256(path) != artifact.get("sha256"):
            issues.append(f"artifact hash mismatch: {artifact['uri']}")
    return {
        "passed": not issues,
        "candidate_sha256": canonical_hash(candidate),
        "issues": issues,
    }
