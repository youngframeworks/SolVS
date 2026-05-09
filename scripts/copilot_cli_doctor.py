#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLEET_CONFIG = ROOT / "config" / "fleet.json"

STATUS_CODE = {
    "ready": 0,
    "missing": 10,
    "install-required": 11,
    "auth-required": 12,
}


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


def resolve_cli_bin() -> str | None:
    configured = os.environ.get("COPILOT_CLI_BIN")
    if configured:
        return configured
    return shutil.which("copilot")


def load_provider() -> dict:
    with FLEET_CONFIG.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("providers", {}).get("copilot-cli", {})


def resolve_backend(provider: dict) -> str:
    return provider.get("backend", os.environ.get("COPILOT_CLI_BACKEND", "copilot-cli")).strip().lower()


def run_command(cmd: list[str], timeout: int, env: dict[str, str] | None = None) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return None


def token_supported(token: str) -> bool:
    return token.startswith("github_pat_") or token.startswith("gho_")


def build_auth_env() -> dict[str, str]:
    env = os.environ.copy()
    token_names = ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
    for name in token_names:
        value = env.get(name, "")
        if not value:
            continue
        if token_supported(value):
            return env
        # Remove unsupported token values (e.g., classic ghp_) for this probe.
        env.pop(name, None)
    gh_bin = shutil.which("gh")
    if gh_bin is None:
        return env
    token_proc = run_command([gh_bin, "auth", "token"], 6, env)
    if token_proc is None:
        return env
    token = token_proc.stdout.strip()
    # Copilot CLI does not accept classic ghp tokens.
    if token_proc.returncode == 0 and token and token_supported(token):
        env.setdefault("COPILOT_GITHUB_TOKEN", token)
    return env


def detect_status(cli_bin: str | None) -> dict:
    result = {
        "status": "unknown",
        "cli": cli_bin,
        "detail": "",
        "recommendation": "",
    }
    provider = load_provider()
    backend = resolve_backend(provider)
    if backend == "foundry-local":
        probe = run_command(
            [
                "python3",
                "scripts/copilot_cli_adapter.py",
                "--agent",
                "SolManager",
                "--task",
                "provider readiness probe",
            ],
            60,
        )
        if probe is None:
            result["status"] = "auth-required"
            result["detail"] = "Foundry-backed Copilot provider timed out during readiness probe."
            result["recommendation"] = "Ensure Foundry Local Qwen is running and responsive."
            return result

        combined_probe = (probe.stdout + "\n" + probe.stderr).strip()
        if probe.returncode == 0 and probe.stdout.strip():
            result["status"] = "ready"
            result["detail"] = probe.stdout.strip()
            result["recommendation"] = "No action required."
            return result

        result["status"] = "auth-required"
        result["detail"] = combined_probe or "Foundry-backed Copilot provider failed readiness probe."
        result["recommendation"] = "Check Foundry Local endpoint and Qwen model availability."
        return result

    if cli_bin is None:
        result["status"] = "missing"
        result["detail"] = "Standalone GitHub Copilot CLI was not found in PATH."
        result["recommendation"] = "Install Copilot CLI and/or set COPILOT_CLI_BIN."
        return result

    version = run_command([cli_bin, "--version"], 6)
    if version is None:
        result["status"] = "auth-required"
        result["detail"] = "Copilot CLI did not respond to --version in time."
        result["recommendation"] = "Ensure Copilot CLI is installed correctly and not blocked by interactive prompts."
        return result

    combined = (version.stdout + "\n" + version.stderr).strip()
    if "Cannot find GitHub Copilot CLI" in combined:
        result["status"] = "install-required"
        result["detail"] = combined
        result["recommendation"] = "Install the standalone GitHub Copilot CLI binary."
        return result

    auth_env = build_auth_env()
    suggest = run_command([
        cli_bin,
        "-p",
        "print working directory",
        "-s",
        "--no-ask-user",
    ], 35, auth_env)

    if suggest is None:
        result["status"] = "auth-required"
        result["detail"] = "Copilot CLI timed out during non-interactive suggest execution."
        result["recommendation"] = "Authenticate Copilot CLI for unattended use."
        return result

    combined = (suggest.stdout + "\n" + suggest.stderr).strip()
    if suggest.returncode == 0 and suggest.stdout.strip():
        result["status"] = "ready"
        result["detail"] = suggest.stdout.strip()
        result["recommendation"] = "No action required."
        return result

    result["status"] = "auth-required"
    result["detail"] = combined or "Copilot CLI failed to provide a non-interactive suggestion."
    result["recommendation"] = "Complete Copilot CLI sign-in/configuration for non-interactive use."
    return result


def print_result(result: dict, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(result))
        return
    if output_format == "plain":
        print(f"COPILOT_STATUS={result['status']}")
        print(f"COPILOT_CLI={result.get('cli')}")
        print(f"DETAIL={result['detail']}")
        print(f"RECOMMENDATION={result['recommendation']}")
        return

    print(f"::notice title=Copilot CLI Status::{result['status']}")
    print(f"::notice title=Copilot CLI Detail::{result['detail']}")
    print(f"::notice title=Copilot CLI Recommendation::{result['recommendation']}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("## Copilot CLI Doctor\n")
            handle.write(f"- status: `{result['status']}`\n")
            handle.write(f"- cli: `{result.get('cli')}`\n")
            handle.write(f"- detail: {result['detail']}\n")
            handle.write(f"- recommendation: {result['recommendation']}\n")


def main():
    parser = argparse.ArgumentParser(description="Classify Copilot CLI readiness for local and CI usage")
    parser.add_argument("--format", choices=["json", "plain", "github"], default="json")
    args = parser.parse_args()

    load_env_file()
    result = detect_status(resolve_cli_bin())
    print_result(result, args.format)
    raise SystemExit(STATUS_CODE.get(result["status"], 20))


if __name__ == "__main__":
    main()
