"""Tool and solver discovery from versioned manifests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from .contracts import ContractValidator


@dataclass(frozen=True)
class RegisteredTool:
    manifest: Mapping[str, Any]
    source: Path
    solver_capability: Mapping[str, Any] | None = None

    @property
    def key(self) -> str:
        return f"{self.manifest['id']}@{self.manifest['version']}"


def _load_document(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(text)
    else:
        payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        raise ValueError(f"manifest must be an object: {path}")
    return payload


class ToolRegistry:
    """Load tools without hard-coded routing by tool name."""

    def __init__(self, validator: ContractValidator | None = None) -> None:
        self.validator = validator or ContractValidator()
        self._tools: dict[str, RegisteredTool] = {}

    def discover(self, roots: Iterable[Path]) -> tuple[RegisteredTool, ...]:
        for root in roots:
            if not root.exists():
                continue
            candidates = sorted(root.rglob("tool-manifest.y*ml"))
            candidates.extend(sorted(root.rglob("tool-manifest.json")))
            for path in candidates:
                self.register(path)
        return self.all()

    def register(self, manifest_path: Path) -> RegisteredTool:
        manifest = _load_document(manifest_path)
        self.validator.validate(manifest, "ToolManifest")
        key = f"{manifest['id']}@{manifest['version']}"
        if key in self._tools:
            raise ValueError(f"duplicate tool registration: {key}")

        capability = None
        capability_ref = manifest.get("solver_capability")
        if capability_ref:
            capability_path = (manifest_path.parent / capability_ref).resolve()
            capability = _load_document(capability_path)
            self.validator.validate(capability, "SolverCapability")
            if capability["solver_id"] != manifest["id"]:
                raise ValueError(
                    f"solver id mismatch: {capability['solver_id']} != {manifest['id']}"
                )

        registered = RegisteredTool(manifest, manifest_path.resolve(), capability)
        self._tools[key] = registered
        return registered

    def all(self) -> tuple[RegisteredTool, ...]:
        return tuple(self._tools[key] for key in sorted(self._tools))

    def get(self, tool_id: str, version: str | None = None) -> RegisteredTool:
        if version is not None:
            return self._tools[f"{tool_id}@{version}"]
        matches = [tool for tool in self._tools.values() if tool.manifest["id"] == tool_id]
        if not matches:
            raise KeyError(tool_id)
        if len(matches) > 1:
            raise KeyError(f"multiple versions registered for {tool_id}; specify one")
        return matches[0]

    def find_by_capability(self, capability: str) -> tuple[RegisteredTool, ...]:
        return tuple(
            tool
            for tool in self.all()
            if capability in tool.manifest["capabilities"]
        )

    def validate_input(
        self, tool: RegisteredTool, document: Mapping[str, Any]
    ) -> None:
        """Validate a tool input using the schema pointer declared by its manifest."""

        schema_ref = str(tool.manifest["input_schema"])
        marker = "#/$defs/"
        if marker not in schema_ref:
            raise ValueError(f"unsupported input schema reference: {schema_ref}")
        schema_name = schema_ref.rsplit(marker, 1)[1]
        self.validator.validate(document, schema_name)

    def compatible_solvers(
        self, contract: Mapping[str, Any]
    ) -> tuple[RegisteredTool, ...]:
        observables = set(contract["objective"]["observables"])
        dimensionality = contract["physics"]["dimensionality"]
        compatible: list[RegisteredTool] = []
        for tool in self.all():
            capability = tool.solver_capability
            if not capability:
                continue
            if dimensionality not in capability["dimensions"]:
                continue
            if observables.issubset(set(capability["observables"])):
                compatible.append(tool)
        return tuple(compatible)
