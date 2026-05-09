#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLEET_CONFIG = ROOT / "config" / "fleet.json"


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


def load_mode() -> str:
    # Env var takes precedence over fleet.json
    env_mode = os.environ.get("COPILOT_CLI_MODE")
    if env_mode:
        return env_mode
    with FLEET_CONFIG.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("providers", {}).get("copilot-cli", {}).get("mode", "auto")


def load_provider() -> dict:
    with FLEET_CONFIG.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("providers", {}).get("copilot-cli", {})


def load_backend_provider(provider: dict) -> dict:
    backend_name = provider.get("backend", os.environ.get("COPILOT_CLI_BACKEND", "copilot-cli"))
    with FLEET_CONFIG.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("providers", {}).get(backend_name, {})


def resolve_cli_bin() -> str | None:
    configured = os.environ.get("COPILOT_CLI_BIN")
    if configured:
        return configured
    return shutil.which("copilot")


def resolve_backend(provider: dict) -> str:
    return provider.get("backend", os.environ.get("COPILOT_CLI_BACKEND", "copilot-cli")).strip().lower()


def token_supported(token: str) -> bool:
    return token.startswith("github_pat_") or token.startswith("gho_")


def ensure_auth_env() -> None:
    token_names = ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
    for name in token_names:
        value = os.environ.get(name, "")
        if not value:
            continue
        if token_supported(value):
            return
        # Avoid poisoning copilot auth with unsupported token types.
        os.environ.pop(name, None)
    gh_bin = shutil.which("gh")
    if gh_bin is None:
        return
    try:
        proc = subprocess.run(
            [gh_bin, "auth", "token"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=6,
        )
    except subprocess.TimeoutExpired:
        return
    token = proc.stdout.strip()
    # Copilot CLI does not accept classic ghp tokens.
    if proc.returncode == 0 and token and token_supported(token):
        os.environ.setdefault("COPILOT_GITHUB_TOKEN", token)


def ci_safe_mode() -> bool:
    return os.environ.get("FLEET_CI_SAFE_MODE", "false").lower() == "true"


def allow_plan_fallback() -> bool:
    return os.environ.get("COPILOT_PLAN_FALLBACK", "false").lower() == "true"


def execution_mode() -> str:
    return os.environ.get("FLEET_EXECUTION_MODE", "proposal").strip().lower()


def copilot_timeout_seconds() -> int:
    raw = os.environ.get("COPILOT_CLI_TIMEOUT_SECONDS", "60").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 60
    return max(10, value)


def build_prompt(task: str, mode: str) -> str:
    base_task = task if mode != "explain" else f"Explain this task briefly and clearly: {task}"
    return (
        "You are SolVS provider adapter output. "
        "Respond in plain text within 6 short lines. "
        "Use only lightweight checks needed for this task; avoid long-running actions. "
        f"Task: {base_task}"
    )


def run_foundry_prompt(task: str, provider: dict, agent: str) -> dict:
    backend = load_backend_provider(provider)
    endpoint = os.environ.get(backend.get("endpointEnv", "FOUNDRY_LOCAL_ENDPOINT"), backend.get("defaultEndpoint", "http://127.0.0.1:5272"))
    model = os.environ.get("FOUNDRY_LOCAL_MODEL", backend.get("model", provider.get("model", "qwen3.5-2b")))
    prompt = build_prompt(task, provider.get("mode", "auto"))
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are SolVS provider output. Be concise and operational."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 512,
            "temperature": 0.3,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{endpoint.rstrip('/')}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=copilot_timeout_seconds()) as response:
            data = json.loads(response.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return {
                "returncode": 0,
                "stdout": content.strip(),
                "stderr": "",
                "backend": "foundry-local",
                "endpoint": endpoint,
                "model": model,
            }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"Foundry chat request failed with HTTP {exc.code}: {detail or exc.reason}",
            "backend": "foundry-local",
            "endpoint": endpoint,
            "model": model,
        }
    except Exception as exc:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"Foundry chat request failed: {exc}",
            "backend": "foundry-local",
            "endpoint": endpoint,
            "model": model,
        }


def fallback_payload(message: str, cli_bin: str | None, mode: str) -> dict:
    return {
        "returncode": 0,
        "stdout": json.dumps(
            {
                "status": "fallback",
                "fallback": "plan-only",
                "reason": message,
                "cli": cli_bin,
                "mode": mode,
            }
        ),
        "stderr": "",
    }


def run_prompt(task: str, cli_bin: str, mode: str) -> dict:
    prompt = build_prompt(task, mode)
    timeout_seconds = copilot_timeout_seconds()
    cmd = [
        cli_bin,
        "-p",
        prompt,
        "--plan",
        "-s",
        "--no-ask-user",
    ]
    # In execute mode, allow non-interactive tool execution to prevent permission stalls.
    if execution_mode() == "execute":
        cmd.append("--allow-all")
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"GitHub Copilot CLI timed out after {timeout_seconds}s. Authenticate or configure the CLI for non-interactive use.",
        }
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def main():
    parser = argparse.ArgumentParser(description="Adapter for GitHub Copilot CLI provider")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    load_env_file()
    provider = load_provider()
    mode = load_mode()
    backend = resolve_backend(provider)
    cli_bin = resolve_cli_bin()
    if backend == "foundry-local":
        result = run_foundry_prompt(args.task, provider, args.agent)
    else:
        ensure_auth_env()
        if cli_bin is None:
            result = {
                "returncode": 1,
                "stdout": "",
                "stderr": "GitHub Copilot CLI is not installed. Set COPILOT_CLI_BIN or install the standalone copilot binary.",
            }
        else:
            result = run_prompt(args.task, cli_bin, mode)

    if result["returncode"] != 0 and provider.get("fallback") == "plan-only" and (allow_plan_fallback() or ci_safe_mode()):
        result = fallback_payload(result["stderr"], cli_bin, mode)

    payload = {
        "agent": args.agent,
        "provider": "copilot-cli",
        "backend": backend,
        "mode": mode,
        "cli": cli_bin,
        **result,
    }
    print(json.dumps(payload))
    raise SystemExit(result["returncode"])


if __name__ == "__main__":
    main()
