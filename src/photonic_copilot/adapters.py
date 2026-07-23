"""SolverAdapter interface and Phase-1 Meep/Lumerical implementations."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .analysis import apply_field_map, build_validation_report, load_arrays, validate_arrays
from .contracts import ContractValidator, canonical_hash


class SolverAdapter(ABC):
    """Boundary between a solver-independent contract and a concrete solver."""

    solver_id: str

    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root.resolve()
        self.validator = ContractValidator(self.repository_root / "schemas/v1/contracts.schema.json")

    @abstractmethod
    def probe_environment(self, *, launch_session: bool = False) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def declare_capabilities(self) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def select_template(self, contract: Mapping[str, Any]) -> Path:
        raise NotImplementedError

    def validate_contract(self, contract: Mapping[str, Any]) -> dict[str, Any]:
        self.validator.validate(contract, "SimulationContract")
        capability = self.declare_capabilities()
        requested = set(contract["objective"]["observables"])
        unsupported = requested - set(capability["observables"])
        if contract["physics"]["dimensionality"] not in capability["dimensions"]:
            return {
                "status": "unsupported",
                "reasons": ["unsupported dimensionality"],
            }
        if unsupported:
            return {
                "status": "unsupported",
                "reasons": [f"unsupported observable: {item}" for item in sorted(unsupported)],
            }
        return {"status": "supported", "reasons": []}

    def generate_model(
        self,
        contract: Mapping[str, Any],
        run_dir: Path,
        *,
        task_id: str,
        run_id: str,
    ) -> dict[str, Any]:
        compatibility = self.validate_contract(contract)
        if compatibility["status"] != "supported":
            raise ValueError(json.dumps(compatibility, ensure_ascii=False))

        run_dir = run_dir.resolve()
        run_dir.mkdir(parents=True, exist_ok=False)
        template = self.select_template(contract)
        script = run_dir / "simulation.py"
        shutil.copy2(template, script)
        helper = template.parent / "_common.py"
        if helper.exists():
            shutil.copy2(helper, run_dir / "_common.py")
        contract_path = run_dir / "simulation-contract.json"
        contract_path.write_text(
            json.dumps(contract, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "schema_id": "RunManifest",
            "schema_version": "1.0",
            "task_id": task_id,
            "run_id": run_id,
            "parent_run": None,
            "solver": self.solver_id,
            "solver_version": None,
            "api_flavor": None,
            "skill_version": "1.0.0",
            "template_id": template.stem,
            "template_version": "1.0.0",
            "contract_hash": canonical_hash(contract),
            "command": None,
            "environment": {},
            "completion_state": "generated",
            "artifacts": [
                {"uri": str(script), "kind": "file", "label": "simulation_script"},
                {"uri": str(contract_path), "kind": "file", "label": "contract"},
            ],
            "warnings": [],
            "error": None,
            "started_at": None,
            "finished_at": None,
        }
        self.validator.validate(manifest, "RunManifest")
        (run_dir / "run-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return manifest

    def preflight(
        self,
        contract: Mapping[str, Any],
        *,
        execution_approval: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        issues: list[str] = []
        if not contract["physics"]["geometry"]:
            issues.append("geometry is empty")
        if not contract["physics"]["materials"]:
            issues.append("materials are empty")
        if execution_approval is None:
            issues.append("G2 execution approval is missing")
        elif execution_approval.get("choice") not in {
            "base_only",
            "base_plus_convergence",
        }:
            issues.append("execution approval has an invalid choice")
        return {"passed": not issues, "issues": issues}

    def execute(
        self,
        run_dir: Path,
        *,
        execution_approval: Mapping[str, Any],
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        if execution_approval.get("approved") is not True:
            raise PermissionError("solver execution requires explicit G2 approval")
        run_dir = run_dir.resolve()
        script = run_dir / "simulation.py"
        contract = json.loads(
            (run_dir / "simulation-contract.json").read_text(encoding="utf-8")
        )
        run_manifest = json.loads(
            (run_dir / "run-manifest.json").read_text(encoding="utf-8")
        )
        command = [
            *self.execution_prefix(contract),
            str(script),
            "--output",
            str(run_dir / "results"),
            *self.execution_arguments(contract, run_manifest["template_id"]),
        ]
        run_manifest["command"] = subprocess.list2cmdline(command)
        run_manifest["started_at"] = datetime.now(timezone.utc).isoformat()
        try:
            completed = subprocess.run(
                command,
                cwd=run_dir,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            (run_dir / "stdout.log").write_text(completed.stdout, encoding="utf-8")
            (run_dir / "stderr.log").write_text(completed.stderr, encoding="utf-8")
            if completed.returncode == 0:
                run_manifest["completion_state"] = "executed"
                run_manifest["error"] = None
            else:
                run_manifest["error"] = {
                    "type": "SolverProcessError",
                    "message": f"solver process exited with code {completed.returncode}",
                }
            return completed
        except subprocess.TimeoutExpired as exc:
            run_manifest["error"] = {
                "type": "TimeoutExpired",
                "message": str(exc),
            }
            raise
        finally:
            run_manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
            run_manifest["artifacts"] = self.package_artifacts(run_dir)
            self.validator.validate(run_manifest, "RunManifest")
            (run_dir / "run-manifest.json").write_text(
                json.dumps(run_manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    def execution_prefix(self, contract: Mapping[str, Any]) -> list[str]:
        del contract
        return [sys.executable]

    def execution_arguments(
        self, contract: Mapping[str, Any], template_name: str
    ) -> list[str]:
        del contract, template_name
        return []

    def extract_raw(
        self,
        result_path: Path,
        field_map: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Load portable solver output and map native names to canonical fields."""

        return apply_field_map(load_arrays(result_path), field_map)

    def analyze(
        self,
        *,
        run_id: str,
        result_path: Path,
        proposed_cases: list[dict[str, Any]],
        convergence_performed: bool,
        user_choice: str,
        previous: Path | None = None,
        field_map: Mapping[str, str] | None = None,
        rt_tolerance: float | None = None,
        convergence_tolerance: float | None = None,
    ) -> dict[str, Any]:
        current = self.extract_raw(result_path, field_map)
        previous_arrays = (
            self.extract_raw(previous, field_map) if previous else None
        )
        raw = validate_arrays(
            current,
            previous=previous_arrays,
            convergence_tolerance=convergence_tolerance,
            rt_tolerance=rt_tolerance,
        )
        report = build_validation_report(
            run_id=run_id,
            raw_report=raw,
            convergence_performed=convergence_performed,
            user_choice=user_choice,
            proposed_cases=proposed_cases,
        )
        self.validator.validate(report, "ValidationReport")
        return report

    def finalize_validation(
        self,
        run_dir: Path,
        report: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Persist validation and apply its permitted completion-state promotion."""

        self.validator.validate(report, "ValidationReport")
        run_dir = run_dir.resolve()
        manifest_path = run_dir / "run-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if report["run_id"] != manifest["run_id"]:
            raise ValueError("ValidationReport run_id does not match RunManifest")
        report_path = run_dir / "validation-report.json"
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        manifest["completion_state"] = report["completion_state"]
        manifest["artifacts"] = self.package_artifacts(run_dir)
        self.validator.validate(manifest, "RunManifest")
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return manifest

    @abstractmethod
    def propose_convergence_cases(
        self, contract: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    def package_artifacts(self, run_dir: Path) -> list[dict[str, Any]]:
        return [
            {"uri": str(path), "kind": "file", "label": path.name}
            for path in sorted(run_dir.rglob("*"))
            if path.is_file()
        ]

    @abstractmethod
    def diagnose(self, failure: str) -> list[str]:
        raise NotImplementedError

    def _run_probe(self, script: Path, extra: list[str] | None = None) -> dict[str, Any]:
        completed = subprocess.run(
            [sys.executable, str(script), *(extra or [])],
            cwd=script.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError:
            return {
                "ok": False,
                "issues": [completed.stderr or completed.stdout or "probe produced no JSON"],
            }


class MeepSolverAdapter(SolverAdapter):
    solver_id = "solver-meep"

    @property
    def workflow_root(self) -> Path:
        return self.repository_root / "meep-fdtd-workflow"

    def probe_environment(self, *, launch_session: bool = False) -> dict[str, Any]:
        del launch_session
        return self._run_probe(self.workflow_root / "scripts/verify_environment.py")

    def declare_capabilities(self) -> Mapping[str, Any]:
        path = self.workflow_root / "solver-capability.yaml"
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def select_template(self, contract: Mapping[str, Any]) -> Path:
        observables = set(contract["objective"]["observables"])
        if observables & {"reflectance", "transmittance"}:
            name = "flux-two-run.py"
        elif "q_factor" in observables:
            name = "resonator-harminv.py"
        elif "far_field" in observables or "mode_coefficients" in observables:
            name = "near2far-mode.py"
        else:
            name = "minimal-waveguide.py"
        return self.workflow_root / "templates" / name

    def propose_convergence_cases(
        self, contract: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        base = contract["numerics"]["mesh"].get("resolution", 20)
        dpml = contract["numerics"]["pml"].get("thickness", 1.0)
        decay = contract["numerics"]["run_control"].get("decay_by", 1e-6)
        return [
            {"kind": "resolution", "values": [base, max(base + 8, int(base * 1.5))]},
            {"kind": "pml_thickness", "values": [dpml, dpml * 1.5]},
            {"kind": "decay_by", "values": [decay, decay * 0.1]},
        ]

    def execution_arguments(
        self, contract: Mapping[str, Any], template_name: str
    ) -> list[str]:
        mesh = contract["numerics"]["mesh"]
        pml = contract["numerics"]["pml"]
        run_control = contract["numerics"]["run_control"]
        arguments = ["--resolution", str(mesh.get("resolution", 20))]
        if template_name == "near2far-mode":
            workflow = (
                "mode"
                if "mode_coefficients" in contract["objective"]["observables"]
                else "near2far"
            )
            arguments.insert(0, workflow)
        if template_name in {"flux-two-run", "resonator-harminv"}:
            arguments += ["--dpml", str(pml.get("thickness", 1.0))]
        if template_name == "flux-two-run":
            arguments += ["--decay-by", str(run_control.get("decay_by", 1e-6))]
        return arguments

    def execution_prefix(self, contract: Mapping[str, Any]) -> list[str]:
        resources = contract["resources"]
        launcher = resources.get("mpi_launcher") or "mpiexec"
        return [
            str(launcher),
            "-n",
            str(resources["mpi_processes"]),
            sys.executable,
        ]

    def diagnose(self, failure: str) -> list[str]:
        return [
            "check Linux/WSL, Conda, Meep, MPI, and HDF5 imports",
            "check units and frequency band",
            "check source, monitor, PML, and field component",
            "check normalization and convergence",
            f"original failure: {failure}",
        ]


class LumericalSolverAdapter(SolverAdapter):
    solver_id = "solver-lumerical-fdtd"

    @property
    def workflow_root(self) -> Path:
        return self.repository_root / "lumerical-fdtd-workflow"

    def probe_environment(self, *, launch_session: bool = False) -> dict[str, Any]:
        extra = ["--launch-session"] if launch_session else []
        return self._run_probe(
            self.workflow_root / "scripts/verify_environment.py", extra
        )

    def declare_capabilities(self) -> Mapping[str, Any]:
        path = self.workflow_root / "solver-capability.yaml"
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def select_template(self, contract: Mapping[str, Any]) -> Path:
        observables = set(contract["objective"]["observables"])
        if observables & {"reflectance", "transmittance"}:
            name = "waveguide-bend-rt.py"
        elif "q_factor" in observables:
            name = "resonator-narrowband.py"
        else:
            name = "minimal-waveguide.py"
        return self.workflow_root / "templates" / name

    def propose_convergence_cases(
        self, contract: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        mesh_accuracy = contract["numerics"]["mesh"].get("accuracy", 2)
        pml_layers = contract["numerics"]["pml"].get("layers", 8)
        shutoff = contract["numerics"]["run_control"].get("auto_shutoff_min", 1e-5)
        return [
            {"kind": "mesh_accuracy", "values": [mesh_accuracy, mesh_accuracy + 1]},
            {"kind": "pml_layers", "values": [pml_layers, pml_layers + 4]},
            {"kind": "auto_shutoff_min", "values": [shutoff, shutoff * 0.1]},
        ]

    def execution_arguments(
        self, contract: Mapping[str, Any], template_name: str
    ) -> list[str]:
        del template_name
        return [
            "--mesh-accuracy",
            str(contract["numerics"]["mesh"].get("accuracy", 2)),
            "--mpi-processes",
            str(contract["resources"]["mpi_processes"]),
        ]

    def diagnose(self, failure: str) -> list[str]:
        return [
            "check ansys.lumerical.core or traditional lumapi import",
            "check license availability and session lifecycle",
            "check SI units, materials, object names, and property order",
            "check source/monitor orientation, mesh, PML, and normalization",
            f"original failure: {failure}",
        ]
