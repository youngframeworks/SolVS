#!/usr/bin/env python3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    proc = subprocess.run(
        ["python3", "scripts/copilot_cli_doctor.py", "--format", "json"],
        cwd=ROOT,
        check=False,
    )
    raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
