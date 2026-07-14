from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_all_solver_templates_parse() -> None:
    paths = list((ROOT / "meep-fdtd-workflow/templates").glob("*.py"))
    paths += list((ROOT / "lumerical-fdtd-workflow/templates").glob("*.py"))
    assert paths
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_lumerical_templates_support_license_free_dry_run(tmp_path: Path) -> None:
    templates = [
        "minimal-waveguide.py",
        "waveguide-bend-rt.py",
        "resonator-narrowband.py",
    ]
    for name in templates:
        script = ROOT / "lumerical-fdtd-workflow/templates" / name
        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "--dry-run",
                "--output",
                str(tmp_path / script.stem),
            ],
            cwd=script.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert (tmp_path / script.stem / "metadata.json").is_file()


def test_reproduce_instructor_has_no_deleted_skill_references() -> None:
    text = (ROOT / "reproduce-instructor/SKILL.md").read_text(encoding="utf-8")
    assert "paper-reproduction-prep" not in text
    assert "../exampleinstructions/" not in text
    for required in ("evidence.json", "targets.json", "simulation-contract.json"):
        assert required in text


def test_workflows_share_platform_completion_states() -> None:
    for directory in ("meep-fdtd-workflow", "lumerical-fdtd-workflow"):
        text = (ROOT / directory / "SKILL.md").read_text(encoding="utf-8")
        for state in ("Generated", "Executed", "Validated"):
            assert state in text
        assert "contracts.schema.json#/$defs/SimulationContract" in text
