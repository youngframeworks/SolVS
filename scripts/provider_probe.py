#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env_file() -> None:
    for candidate in (ROOT / ".env", ROOT / ".env.example"):
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def run_probe(command: list[str]) -> dict:
    proc = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def main():
    load_env_file()
    copilot_bin = os.environ.get("COPILOT_CLI_BIN") or shutil.which("copilot")
    results = {
        "copilotCli": run_probe(["python3", "scripts/copilot_auth_check.py"]),
        "foundryLocal": run_probe([
            "python3",
            "scripts/foundry_local_adapter.py",
            "--agent",
            "SolOSImplementer",
            "--task",
            "provider probe",
        ]),
        "mcp": run_probe(["python3", "scripts/mcp_probe.py"]),
    }
    print(json.dumps(results, indent=2))
    if os.environ.get("FLEET_CI_SAFE_MODE", "false").lower() == "true":
        return
    if results["copilotCli"]["returncode"] != 0:
        raise SystemExit(1)
    if results["foundryLocal"]["returncode"] != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
