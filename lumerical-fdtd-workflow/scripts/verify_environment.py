"""Report whether Python can import and optionally launch Lumerical FDTD."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import platform
import sys
import warnings
from pathlib import Path
from types import ModuleType
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check the Lumerical Python API without consuming a license by "
            "default. Session launch requires --launch-session."
        )
    )
    parser.add_argument(
        "--api-path",
        type=Path,
        help="directory containing a traditional installation-provided lumapi module",
    )
    parser.add_argument(
        "--launch-session",
        action="store_true",
        help="launch and close FDTD to test solver/license access",
    )
    parser.add_argument(
        "--show-gui",
        action="store_true",
        help="show the FDTD GUI during --launch-session (hidden by default)",
    )
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    return parser.parse_args()


def package_version() -> str | None:
    for distribution in ("ansys-lumerical-core", "ansys.lumerical.core"):
        try:
            return importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            continue
    return None


def import_api(api_path: Path | None) -> tuple[ModuleType | None, dict[str, Any]]:
    attempts: list[dict[str, str]] = []
    import_warnings: list[str] = []
    if api_path is not None:
        resolved = api_path.expanduser().resolve()
        if not resolved.is_dir():
            attempts.append(
                {"module": "lumapi", "error": f"API path is not a directory: {resolved}"}
            )
        else:
            sys.path.insert(0, str(resolved))

    for module_name, flavor in (
        ("ansys.lumerical.core", "ansys.lumerical.core"),
        ("lumapi", "traditional lumapi"),
    ):
        module: ModuleType | None = None
        error: Exception | None = None
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                module = importlib.import_module(module_name)
            except Exception as exc:  # preserve import/native errors below
                error = exc
        import_warnings.extend(
            f"{item.category.__name__}: {item.message}" for item in caught
        )

        if module is not None:
            return module, {
                "flavor": flavor,
                "module": module_name,
                "module_path": str(getattr(module, "__file__", "")),
                "package_version": package_version(),
                "attempts": attempts,
                "warnings": import_warnings,
            }
        if error is not None:
            attempts.append(
                {
                    "module": module_name,
                    "error": f"{type(error).__name__}: {error}",
                }
            )

    return None, {"attempts": attempts, "warnings": import_warnings}


def launch_session(api: ModuleType, show_gui: bool) -> dict[str, Any]:
    session = None
    try:
        session = api.FDTD(hide=not show_gui)
        version: Any = None
        getversion = getattr(session, "getversion", None)
        if callable(getversion):
            version = getversion()
        return {
            "ok": True,
            "hidden": not show_gui,
            "solver_version": str(version) if version is not None else None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "hidden": not show_gui,
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if session is not None:
            close = getattr(session, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {
        "ok": False,
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "python": sys.version,
        "executable": sys.executable,
        "api": None,
        "session_test": {
            "requested": bool(args.launch_session),
            "performed": False,
        },
        "issues": [],
    }

    api, api_report = import_api(args.api_path)
    report["api"] = api_report
    if api is None:
        report["issues"].append(
            "No supported Lumerical Python API could be imported. Use the API "
            "shipped with the installed Lumerical release; do not install an "
            "unrelated public package named lumapi."
        )
    elif not hasattr(api, "FDTD"):
        report["issues"].append("Imported API does not expose an FDTD session class.")

    if api is not None and hasattr(api, "FDTD") and args.launch_session:
        session_report = launch_session(api, args.show_gui)
        session_report["requested"] = True
        session_report["performed"] = True
        report["session_test"] = session_report
        if not session_report["ok"]:
            report["issues"].append(
                "FDTD session launch failed; inspect installation, license, and "
                "interop configuration."
            )

    report["ok"] = not report["issues"]
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
