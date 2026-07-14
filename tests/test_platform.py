from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from jsonschema import Draft202012Validator

from photonic_copilot.adapters import LumericalSolverAdapter, MeepSolverAdapter
from photonic_copilot.analysis import build_validation_report, validate_arrays
from photonic_copilot.contracts import (
    ContractValidationError,
    ContractValidator,
    canonical_hash,
)
from photonic_copilot.example_library import ExampleLibrary
from photonic_copilot.gates import (
    Approval,
    QualityGateError,
    completion_state,
    require_execution_gate,
)
from photonic_copilot.orchestrator import WorkflowSession
from photonic_copilot.registry import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]


def load_contract() -> dict:
    return json.loads(
        (ROOT / "benchmarks/waveguide-bend-rt/simulation-contract.json").read_text(
            encoding="utf-8"
        )
    )


def validated_report(run_id: str = "run-1") -> dict:
    raw = {
        "passed": True,
        "checks": [
            {
                "check": "lossless_rt_balance",
                "passed": True,
                "tolerance": 0.05,
                "worst_absolute_error": 0.0,
            }
        ],
        "failures": [],
        "worst_relative_difference": 0.01,
    }
    return build_validation_report(
        run_id=run_id,
        raw_report=raw,
        convergence_performed=True,
        user_choice="base_plus_convergence",
        proposed_cases=[{"kind": "mesh", "values": [20, 30]}],
    )


def test_schema_catalog_and_contract() -> None:
    validator = ContractValidator()
    Draft202012Validator.check_schema(validator.catalog)
    contract = load_contract()
    validator.validate(contract)
    assert len(canonical_hash(contract)) == 64


def test_unaccepted_assumption_is_rejected() -> None:
    contract = load_contract()
    contract["assumptions"] = [
        {
            "parameter_id": "material.core",
            "reason": "paper omitted dispersion",
            "consequence": "resonance can shift",
            "accepted": False,
            "accepted_by": None,
            "evidence_id": None,
        }
    ]
    with pytest.raises(ContractValidationError, match="require acceptance"):
        ContractValidator().validate(contract)


def test_registry_discovers_workflow_and_two_solvers() -> None:
    registry = ToolRegistry()
    tools = registry.discover([ROOT])
    assert {tool.manifest["id"] for tool in tools} == {
        "example-library",
        "fdtd-result-validation",
        "free-design-intake",
        "paper-reproduction-instructor",
        "solver-meep",
        "solver-lumerical-fdtd",
    }
    compatible = registry.compatible_solvers(load_contract())
    assert {tool.manifest["id"] for tool in compatible} == {
        "solver-meep",
        "solver-lumerical-fdtd",
    }
    registry.validate_input(registry.get("solver-meep"), load_contract())


def test_adapters_map_same_contract(tmp_path: Path) -> None:
    contract = load_contract()
    meep = MeepSolverAdapter(ROOT)
    lumerical = LumericalSolverAdapter(ROOT)
    assert meep.validate_contract(contract)["status"] == "supported"
    assert lumerical.validate_contract(contract)["status"] == "supported"

    meep_manifest = meep.generate_model(
        contract, tmp_path / "meep", task_id="task", run_id="meep-run"
    )
    lum_manifest = lumerical.generate_model(
        contract, tmp_path / "lumerical", task_id="task", run_id="lum-run"
    )
    assert meep_manifest["contract_hash"] == lum_manifest["contract_hash"]
    assert Path(meep_manifest["artifacts"][0]["uri"]).name == "simulation.py"
    assert (tmp_path / "lumerical/_common.py").is_file()
    assert lum_manifest["template_id"] == "waveguide-bend-rt"
    assert meep.execution_arguments(contract, "flux-two-run") == [
        "--resolution",
        "20",
        "--dpml",
        "1.0",
        "--decay-by",
        "1e-06",
    ]
    assert lumerical.execution_arguments(contract, "waveguide-bend-rt") == [
        "--mesh-accuracy",
        "2",
    ]
    report = validated_report("lum-run")
    finalized = lumerical.finalize_validation(tmp_path / "lumerical", report)
    assert finalized["completion_state"] == "validated"
    assert (tmp_path / "lumerical/validation-report.json").is_file()


def test_two_workflow_modes_share_contract_and_solver_capabilities(
    tmp_path: Path,
) -> None:
    registry = ToolRegistry()
    registry.discover([ROOT])
    common = {
        "schema_id": "WorkflowRequest",
        "schema_version": "1.0",
        "input_refs": [{"uri": "input.json", "kind": "file"}],
        "requested_solver": None,
        "user_constraints": {},
        "created_at": "2026-07-14T08:00:00Z",
    }
    paper = WorkflowSession(
        {
            **common,
            "workflow_id": "paper-workflow",
            "mode": "paper_reproduction",
        },
        tmp_path / "paper",
        registry,
    )
    design = WorkflowSession(
        {
            **common,
            "workflow_id": "design-workflow",
            "mode": "free_design",
        },
        tmp_path / "design",
        registry,
    )
    assert paper.plan_for_mode()[0] == "paper_evidence_extraction"
    assert design.plan_for_mode()[0] == "requirement_intake"
    assert paper.plan_for_mode()[-1] == design.plan_for_mode()[-1] == "fdtd_simulation"


def test_common_analysis_and_completion_state() -> None:
    wavelength = np.linspace(1.5, 1.6, 20)
    reflectance = 0.1 + 0.01 * np.sin(np.linspace(0, np.pi, 20))
    transmittance = 1.0 - reflectance
    report = validate_arrays(
        {
            "wavelength": wavelength,
            "reflectance": reflectance,
            "transmittance": transmittance,
        },
        rt_tolerance=1e-10,
    )
    assert report["passed"]
    assert (
        completion_state(
            solver_executed=True,
            outputs_readable=True,
            convergence_performed=False,
            all_checks_passed=True,
        )
        == "executed"
    )


def test_execution_gate_requires_recorded_choice() -> None:
    with pytest.raises(QualityGateError):
        require_execution_gate(
            Approval(gate="G2", approved=True, reviewer="expert", rationale="ok")
        )
    assert (
        require_execution_gate(
            Approval(
                gate="G2",
                approved=True,
                reviewer="expert",
                rationale="approved resources",
                choice="base_only",
            )
        )
        == "base_only"
    )


def test_example_library_publishes_immutable_version(tmp_path: Path) -> None:
    artifact = tmp_path / "run" / "spectra.json"
    artifact.parent.mkdir()
    artifact.write_text('{"transmittance": [1.0]}', encoding="utf-8")
    manifest = {
        "schema_id": "ExampleManifest",
        "schema_version": "1.0",
        "example_id": "waveguide-example",
        "version": "1.0.0",
        "mode": "free_design",
        "quality": "reviewed",
        "paper_manifest": None,
        "evidence": None,
        "targets": None,
        "simulation_contract": "contract.json",
        "run_manifest": "run-manifest.json",
        "validation_report": "validation-report.json",
        "artifacts": [{"uri": str(artifact), "kind": "file"}],
        "device_type": "waveguide_bend",
        "materials": ["benchmark_dielectric"],
        "observables": ["reflectance", "transmittance"],
        "solver": "solver-meep",
        "tags": [],
        "reviewer": None,
        "parent_example": None,
        "license": None,
        "sensitivity": "internal",
    }
    candidate = {
        "schema_id": "ExampleCandidate",
        "schema_version": "1.0",
        "candidate_id": "candidate-1",
        "source_run_id": "run-1",
        "status": "pending_review",
        "manifest_draft": manifest,
        "integrity_checks": [],
        "license_check": {"passed": True},
        "sensitivity": "internal",
        "failure_labels": [],
        "submitted_at": "2026-07-14T08:00:00Z",
        "submitted_by": "agent",
    }
    library = ExampleLibrary(tmp_path / "library")
    library.stage_candidate(candidate)
    published = library.publish(
        candidate,
        validation_report=validated_report(),
        approval=Approval(
            gate="G3",
            approved=True,
            reviewer="expert",
            rationale="validated and complete",
        ),
    )
    assert published["reviewer"] == "expert"
    assert library.search(device_type="waveguide_bend")[0]["quality"] == "reviewed"
    with pytest.raises(FileExistsError):
        library.publish(
            candidate,
            validation_report=validated_report(),
            approval=Approval(
                gate="G3",
                approved=True,
                reviewer="expert",
                rationale="duplicate",
            ),
        )


def test_cross_solver_static_benchmark(tmp_path: Path) -> None:
    wavelength = np.linspace(1.5e-6, 1.6e-6, 50)
    reflectance = 0.08 + 0.02 * np.sin(np.linspace(0, 2 * np.pi, 50))
    transmittance = 1.0 - reflectance
    meep = tmp_path / "meep.npz"
    lum = tmp_path / "lumerical.npz"
    np.savez(
        meep,
        wavelength=wavelength,
        reflectance=reflectance,
        transmittance=transmittance,
    )
    np.savez(
        lum,
        wavelength=wavelength[::-1],
        reflectance=(reflectance * 0.99)[::-1],
        transmittance=(1.0 - reflectance * 0.99)[::-1],
    )
    script = ROOT / "fdtd-core/benchmarks/compare_cross_solver.py"
    completed = subprocess.run(
        [sys.executable, str(script), str(meep), str(lum)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout)["passed"]
