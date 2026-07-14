"""Report whether the current Python environment can use PyMeep."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report: dict[str, object] = {
        "ok": False,
        "platform": platform.platform(),
        "system": platform.system(),
        "python": sys.version,
        "executable": sys.executable,
        "issues": [],
    }

    if platform.system() == "Windows":
        report["issues"].append(
            "Native Windows is unsupported by Meep; run inside Linux/WSL."
        )

    try:
        import meep as mp
        import h5py
        import numpy as np

        # Exercise commonly required API objects without starting a simulation.
        vector = mp.Vector3(1, 2, 0)
        medium = mp.Medium(epsilon=2.25)
        report.update(
            {
                "meep": mp.__version__,
                "numpy": np.__version__,
                "h5py": h5py.__version__,
                "hdf5": h5py.version.hdf5_version,
                "mpi_processes": mp.count_processors(),
                "single_precision": bool(mp.is_single_precision()),
                "api_smoke": {
                    "vector": [vector.x, vector.y, vector.z],
                    "epsilon_at_1": complex(medium.epsilon(1.0)[0, 0]).real,
                },
            }
        )
    except Exception as exc:  # environment diagnostics must report import/ABI errors
        report["issues"].append(f"{type(exc).__name__}: {exc}")

    report["ok"] = not report["issues"]
    rendered = json.dumps(report, indent=2)
    print(rendered)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
