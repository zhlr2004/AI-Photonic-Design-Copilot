"""Recoverable tool lifecycle records for the two workflow modes."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .contracts import ContractValidator
from .registry import RegisteredTool, ToolRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowSession:
    """Persist tool calls independently so a workflow can resume safely."""

    def __init__(
        self,
        workflow_request: Mapping[str, Any],
        workspace: Path,
        registry: ToolRegistry,
    ) -> None:
        self.validator = ContractValidator()
        self.validator.validate(workflow_request, "WorkflowRequest")
        self.request = dict(workflow_request)
        self.registry = registry
        self.workspace = workspace.resolve()
        self.workspace.mkdir(parents=True, exist_ok=False)
        (self.workspace / "workflow-request.json").write_text(
            json.dumps(self.request, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @property
    def mode(self) -> str:
        return str(self.request["mode"])

    def plan_for_mode(self) -> tuple[str, ...]:
        if self.mode == "paper_reproduction":
            return (
                "paper_evidence_extraction",
                "example_search",
                "simulation_contract_drafting",
                "fdtd_simulation",
            )
        return (
            "requirement_intake",
            "example_search",
            "simulation_contract_drafting",
            "fdtd_simulation",
        )

    def call(
        self,
        tool: RegisteredTool,
        input_refs: list[dict[str, Any]],
        operation: Callable[[], list[dict[str, Any]]],
        *,
        approval_ref: str | None = None,
    ) -> dict[str, Any]:
        call_id = f"toolcall-{uuid.uuid4()}"
        record: dict[str, Any] = {
            "schema_id": "ToolCallRecord",
            "schema_version": "1.0",
            "tool_call_id": call_id,
            "tool_id": tool.manifest["id"],
            "tool_version": tool.manifest["version"],
            "workflow_id": self.request["workflow_id"],
            "input_refs": input_refs,
            "output_refs": [],
            "started_at": _now(),
            "finished_at": None,
            "status": "running",
            "approval_ref": approval_ref,
            "error": None,
        }
        path = self.workspace / f"{call_id}.json"
        self._write_record(path, record)
        try:
            record["output_refs"] = operation()
            record["status"] = "succeeded"
        except Exception as exc:
            record["status"] = "failed"
            record["error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
            }
            raise
        finally:
            record["finished_at"] = _now()
            self._write_record(path, record)
        return record

    def completed_calls(self) -> tuple[dict[str, Any], ...]:
        records: list[dict[str, Any]] = []
        for path in sorted(self.workspace.glob("toolcall-*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            self.validator.validate(record, "ToolCallRecord")
            if record["status"] == "succeeded":
                records.append(record)
        return tuple(records)

    def last_successful_capability(self) -> str | None:
        calls = self.completed_calls()
        if not calls:
            return None
        tool = self.registry.get(calls[-1]["tool_id"], calls[-1]["tool_version"])
        capabilities = tool.manifest["capabilities"]
        return capabilities[-1] if capabilities else None

    def _write_record(self, path: Path, record: Mapping[str, Any]) -> None:
        self.validator.validate(record, "ToolCallRecord")
        path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
