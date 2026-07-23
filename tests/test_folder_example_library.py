from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from photonic_copilot.contracts import canonical_hash
from photonic_copilot.curation import inspect_case, prepare_case
from photonic_copilot.folder_example_library import FolderExampleLibrary, tree_snapshot
from photonic_copilot.gates import Approval


ROOT = Path(__file__).resolve().parents[1]


def contract() -> dict:
    return json.loads(
        (ROOT / "benchmarks/waveguide-bend-rt/simulation-contract.json").read_text(
            encoding="utf-8"
        )
    )


def validation_report() -> dict:
    return {
        "schema_id": "ValidationReport",
        "schema_version": "1.0",
        "validation_id": "validation-run-legacy",
        "run_id": "run-legacy",
        "completion_state": "validated",
        "convergence": {
            "performed": True,
            "user_choice": "base_plus_convergence",
            "proposed_cases": [{"kind": "mesh", "values": [20, 30]}],
            "executed_cases": [{"kind": "mesh", "values": [20, 30]}],
            "worst_relative_difference": 0.01,
        },
        "checks": [
            {
                "name": "energy_balance",
                "method": "deterministic_python",
                "passed": True,
                "threshold": 0.05,
                "value": 0.01,
                "input_refs": [],
                "details": {},
            }
        ],
        "passed": True,
        "warnings": [],
        "limitations": [],
    }


def run_manifest() -> dict:
    return {
        "schema_id": "RunManifest",
        "schema_version": "1.0",
        "task_id": "task-legacy",
        "run_id": "run-legacy",
        "parent_run": None,
        "solver": "solver-meep",
        "solver_version": "test",
        "api_flavor": None,
        "skill_version": "1.0.0",
        "template_id": "legacy",
        "template_version": "1.0.0",
        "contract_hash": canonical_hash(contract()),
        "command": "mpiexec -n 1 python simulation.py",
        "environment": {},
        "completion_state": "validated",
        "artifacts": [],
        "warnings": [],
        "error": None,
        "started_at": None,
        "finished_at": None,
    }


def make_legacy_case(path: Path) -> None:
    path.mkdir()
    legacy_contract = contract()
    legacy_contract["legacy_note"] = "remove during curation"
    (path / "simulation-contract.json").write_text(
        json.dumps(legacy_contract), encoding="utf-8"
    )
    (path / "run-manifest.json").write_text(
        json.dumps(run_manifest()), encoding="utf-8"
    )
    (path / "validation-report.json").write_text(
        json.dumps(validation_report()), encoding="utf-8"
    )
    (path / "simulation.py").write_text("print('simulation')\n", encoding="utf-8")
    (path / "spectrum.csv").write_text("wavelength,T\n1.55,0.9\n", encoding="utf-8")
    cache = path / "__pycache__"
    cache.mkdir()
    (cache / "ignored.pyc").write_bytes(b"cache")


def test_library_root_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    environment_root = tmp_path / "from-env"
    monkeypatch.setenv("PHOTONIC_EXAMPLE_LIBRARY_ROOT", str(environment_root))
    assert FolderExampleLibrary().root == environment_root.resolve()
    explicit = tmp_path / "explicit"
    assert FolderExampleLibrary(explicit).root == explicit.resolve()
    monkeypatch.delenv("PHOTONIC_EXAMPLE_LIBRARY_ROOT")
    project = tmp_path / "project"
    assert FolderExampleLibrary(project_root=project).root == (
        project / "example-library"
    ).resolve()


def test_inspection_is_read_only_and_reports_exclusions(tmp_path: Path) -> None:
    source = tmp_path / "legacy"
    make_legacy_case(source)
    before = tree_snapshot(source)["tree_sha256"]
    snapshot, plan = inspect_case(
        source, candidate_id="legacy-001", mode="free_design"
    )
    after = tree_snapshot(source)["tree_sha256"]
    assert before == after == snapshot["tree_sha256"]
    assert not plan["blocked"]
    assert any(
        item["action"] == "exclude" and "__pycache__" in item["path"]
        for item in plan["items"]
    )


def test_sensitive_source_is_blocked(tmp_path: Path) -> None:
    source = tmp_path / "secret-case"
    source.mkdir()
    (source / "config.txt").write_text(
        "api_key='abcdefghijklmnop'\n", encoding="utf-8"
    )
    _, plan = inspect_case(
        source, candidate_id="secret-001", mode="paper_reproduction"
    )
    assert plan["blocked"]
    assert any(item["action"] == "blocked" for item in plan["items"])


def test_source_symlink_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "linked-case"
    source.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    link = source / "escape.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable on this Windows configuration")
    with pytest.raises(ValueError, match="symbolic links"):
        inspect_case(source, candidate_id="linked-001", mode="free_design")


def test_prepare_publish_rebuild_and_move_folder_library(tmp_path: Path) -> None:
    source = tmp_path / "legacy"
    make_legacy_case(source)
    source_before = tree_snapshot(source)["tree_sha256"]
    _, plan = inspect_case(
        source, candidate_id="legacy-001", mode="free_design"
    )
    library = FolderExampleLibrary(tmp_path / "library")
    staging = prepare_case(
        source,
        library=library,
        candidate_id="legacy-001",
        mode="free_design",
        target_version="1.0.0",
        plan=plan,
        metadata={
            "example_id": "legacy-waveguide",
            "quality": "validated",
            "solver": "solver-meep",
            "device_type": "waveguide_bend",
            "materials": ["benchmark_dielectric"],
            "observables": ["reflectance", "transmittance"],
            "sensitivity": "internal",
            "license_check": {"passed": True, "notes": "owned internal case"},
        },
    )
    assert tree_snapshot(source)["tree_sha256"] == source_before
    assert not (staging / "payload/legacy-source").exists()
    candidate = json.loads(
        (staging / "example-candidate.json").read_text(encoding="utf-8")
    )
    cleaning = json.loads(
        (staging / "cleaning-report.json").read_text(encoding="utf-8")
    )
    assert any(item["field"] == "legacy_note" for item in cleaning["removed_fields"])
    skill_scripts = (
        ROOT / "curate-photonic-example-case/scripts"
    )
    validation_cli = subprocess.run(
        [
            sys.executable,
            str(skill_scripts / "validate_candidate.py"),
            "--candidate-dir",
            str(staging),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert validation_cli.returncode == 0, validation_cli.stderr
    sensitive_cli = subprocess.run(
        [
            sys.executable,
            str(skill_scripts / "scan_sensitive.py"),
            "--candidate-dir",
            str(staging),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert sensitive_cli.returncode == 0, sensitive_cli.stderr
    candidate_hash = canonical_hash(candidate)
    approval = Approval(
        gate="G3",
        approved=True,
        reviewer="expert",
        rationale="curated candidate is complete",
        details={"candidate_sha256": candidate_hash},
    )
    manifest = library.publish(
        "legacy-001",
        validation_report=validation_report(),
        approval=approval,
    )
    assert manifest["quality"] == "validated"
    assert all(not Path(item["uri"]).is_absolute() for item in manifest["artifacts"])
    assert library.search(device_type="waveguide_bend")[0]["example_id"] == (
        "legacy-waveguide"
    )
    assert library.verify_library() == []

    library.catalog_path.unlink()
    rebuilt = library.rebuild_catalog()
    assert len(rebuilt["entries"]) == 1

    moved = tmp_path / "moved-library"
    shutil.copytree(library.root, moved)
    moved_library = FolderExampleLibrary(moved)
    assert moved_library.get("legacy-waveguide", "1.0.0")["quality"] == "validated"


def test_g3_candidate_hash_and_version_are_immutable(tmp_path: Path) -> None:
    source = tmp_path / "legacy"
    make_legacy_case(source)
    _, plan = inspect_case(
        source, candidate_id="legacy-002", mode="free_design"
    )
    library = FolderExampleLibrary(tmp_path / "library")
    prepare_case(
        source,
        library=library,
        candidate_id="legacy-002",
        mode="free_design",
        target_version="1.0.0",
        plan=plan,
        metadata={
            "quality": "validated",
            "license_check": {"passed": True},
        },
    )
    wrong_approval = Approval(
        gate="G3",
        approved=True,
        reviewer="expert",
        rationale="wrong snapshot",
        details={"candidate_sha256": "0" * 64},
    )
    with pytest.raises(ValueError, match="not bound"):
        library.publish(
            "legacy-002",
            validation_report=validation_report(),
            approval=wrong_approval,
        )


def test_curator_cli_inspect_and_dry_run_write_no_library_files(
    tmp_path: Path,
) -> None:
    source = tmp_path / "legacy"
    make_legacy_case(source)
    script = (
        ROOT
        / "curate-photonic-example-case/scripts/curate_case.py"
    )
    inspect = subprocess.run(
        [
            sys.executable,
            str(script),
            "inspect",
            "--source",
            str(source),
            "--candidate-id",
            "legacy-cli",
            "--mode",
            "free_design",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert inspect.returncode == 0, inspect.stderr
    payload = json.loads(inspect.stdout)
    plan_path = tmp_path / "inspection.json"
    plan_path.write_text(json.dumps(payload), encoding="utf-8")
    library_root = tmp_path / "dry-library"
    dry_run = subprocess.run(
        [
            sys.executable,
            str(script),
            "prepare",
            "--source",
            str(source),
            "--library-root",
            str(library_root),
            "--candidate-id",
            "legacy-cli",
            "--mode",
            "free_design",
            "--plan",
            str(plan_path),
            "--dry-run",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert dry_run.returncode == 0, dry_run.stderr
    assert not library_root.exists()


def test_legacy_sqlite_import_is_read_only_and_stages_only(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy-sqlite"
    legacy.mkdir()
    artifact = legacy / "legacy.py"
    artifact.write_text("print('legacy')\n", encoding="utf-8")
    manifest = {
        "schema_id": "ExampleManifest",
        "schema_version": "1.0",
        "example_id": "old-example",
        "version": "1.0.0",
        "mode": "free_design",
        "quality": "executed",
        "paper_manifest": None,
        "evidence": None,
        "targets": None,
        "simulation_contract": None,
        "run_manifest": None,
        "validation_report": None,
        "artifacts": [{"uri": "legacy.py", "kind": "file"}],
        "device_type": "waveguide",
        "materials": [],
        "observables": [],
        "solver": None,
        "tags": [],
        "reviewer": None,
        "parent_example": None,
        "license": None,
        "sensitivity": "internal",
    }
    database = legacy / "examples.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE examples (example_id TEXT, version TEXT, quality TEXT, "
            "manifest_json TEXT, PRIMARY KEY(example_id, version))"
        )
        connection.execute(
            "INSERT INTO examples VALUES (?, ?, ?, ?)",
            ("old-example", "1.0.0", "executed", json.dumps(manifest)),
        )
    before = tree_snapshot(legacy)["tree_sha256"]
    library = FolderExampleLibrary(tmp_path / "new-library")
    staging = library.stage_legacy_sqlite_example(
        legacy,
        example_id="old-example",
        version="1.0.0",
        candidate_id="old-example-import",
    )
    after = tree_snapshot(legacy)["tree_sha256"]
    assert before == after
    candidate = json.loads(
        (staging / "example-candidate.json").read_text(encoding="utf-8")
    )
    assert candidate["manifest_draft"]["quality"] == "archived"
    assert "legacy-import" in candidate["manifest_draft"]["tags"]
    assert not (library.examples_root / "old-example").exists()


def test_human_reviewed_archived_case_can_publish_without_solver_report(
    tmp_path: Path,
) -> None:
    source = tmp_path / "human-reviewed"
    source.mkdir()
    (source / "simulation.py").write_text("print('reviewed')\n", encoding="utf-8")
    (source / "human-review.md").write_text(
        "# Human review\n\nScientific content reviewed.\n", encoding="utf-8"
    )
    _, plan = inspect_case(
        source, candidate_id="reviewed-archive", mode="free_design"
    )
    library = FolderExampleLibrary(tmp_path / "library")
    staging = prepare_case(
        source,
        library=library,
        candidate_id="reviewed-archive",
        mode="free_design",
        target_version="1.0.0",
        plan=plan,
        metadata={
            "quality": "archived",
            "license_check": {"passed": True, "notes": "owned source"},
            "tags": ["human-reviewed"],
        },
    )
    candidate = json.loads(
        (staging / "example-candidate.json").read_text(encoding="utf-8")
    )
    decision = {
        "schema_id": "G3ReviewDecision",
        "schema_version": "1.0",
        "candidate_id": "reviewed-archive",
        "candidate_sha256": canonical_hash(candidate),
        "approved": True,
        "reviewer": "domain-expert",
        "reviewed_at": "2026-07-17T09:00:00Z",
        "rationale": "Prior review retained; normalized archival copy confirmed.",
        "approved_quality": "archived",
        "allow_publication": True,
    }
    manifest = library.publish_reviewed(
        "reviewed-archive",
        decision=decision,
    )
    final = (
        library.examples_root
        / manifest["example_id"]
        / manifest["version"]
    )
    assert manifest["quality"] == "archived"
    assert (final / "documents/g3-review-decision.json").is_file()
