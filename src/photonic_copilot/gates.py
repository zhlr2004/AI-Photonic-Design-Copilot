"""Human approval and completion-state quality gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class Approval:
    gate: str
    approved: bool
    reviewer: str
    rationale: str
    choice: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "approved": self.approved,
            "reviewer": self.reviewer,
            "rationale": self.rationale,
            "choice": self.choice,
            "details": dict(self.details),
            "created_at": self.created_at,
        }


class QualityGateError(PermissionError):
    pass


def require_contract_gate(
    contract: Mapping[str, Any], approval: Approval
) -> None:
    if approval.gate != "G1" or not approval.approved:
        raise QualityGateError("G1 contract approval is required")
    unaccepted = [
        item["parameter_id"]
        for item in contract["assumptions"]
        if not item["accepted"]
    ]
    if unaccepted:
        raise QualityGateError(
            "contract contains unaccepted assumptions: " + ", ".join(unaccepted)
        )
    resources = contract.get("resources", {})
    execution_mode = resources.get("execution_mode")
    mpi_processes = resources.get("mpi_processes")
    if execution_mode not in {"single_mpi_process", "multi_mpi_process"}:
        raise QualityGateError("G1 must select single or multiple MPI processes")
    if execution_mode == "single_mpi_process" and mpi_processes != 1:
        raise QualityGateError("single_mpi_process requires mpi_processes=1")
    if execution_mode == "multi_mpi_process" and (
        not isinstance(mpi_processes, int) or mpi_processes < 2
    ):
        raise QualityGateError("multi_mpi_process requires mpi_processes>=2")
    cpu_cores = resources.get("cpu_cores")
    if cpu_cores is not None and mpi_processes > cpu_cores:
        raise QualityGateError("G1 MPI process count exceeds declared CPU cores")
    approved_mode = approval.details.get("execution_mode")
    approved_processes = approval.details.get("mpi_processes")
    if approved_mode != execution_mode or approved_processes != mpi_processes:
        raise QualityGateError(
            "G1 approval must record the contract MPI mode and process count"
        )


def require_execution_gate(approval: Approval) -> str:
    if approval.gate != "G2" or not approval.approved:
        raise QualityGateError("G2 execution approval is required")
    if approval.choice not in {"base_only", "base_plus_convergence"}:
        raise QualityGateError("G2 must record base_only or base_plus_convergence")
    return approval.choice


def require_result_gate(
    validation_report: Mapping[str, Any], approval: Approval
) -> None:
    if approval.gate != "G3" or not approval.approved:
        raise QualityGateError("G3 result approval is required")
    if validation_report["completion_state"] == "generated":
        raise QualityGateError("generated-only runs cannot be published as examples")


def require_skill_update_gate(
    experience_record: Mapping[str, Any],
    approval: Approval,
    *,
    regression_passed: bool,
) -> None:
    if approval.gate != "G4" or not approval.approved:
        raise QualityGateError("G4 skill update approval is required")
    if experience_record["review_status"] != "approved":
        raise QualityGateError("ExperienceRecord must be approved")
    if not regression_passed:
        raise QualityGateError("skill regression suite must pass")


def completion_state(
    *,
    solver_executed: bool,
    outputs_readable: bool,
    convergence_performed: bool,
    all_checks_passed: bool,
) -> str:
    if not solver_executed or not outputs_readable:
        return "generated"
    if convergence_performed and all_checks_passed:
        return "validated"
    return "executed"
