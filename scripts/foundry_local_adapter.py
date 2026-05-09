#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Ensure the user-installed SDK is importable on Debian systems
_SDK_SITE = Path.home() / ".local" / "lib"
for _p in _SDK_SITE.glob("python*/site-packages"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

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


def load_provider() -> dict:
    with FLEET_CONFIG.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("providers", {}).get("foundry-local", {})


def resolve_endpoint(provider: dict) -> str:
    env_name = provider.get("endpointEnv", "FOUNDRY_LOCAL_ENDPOINT")
    return os.environ.get(env_name, provider.get("defaultEndpoint", "http://127.0.0.1:5272"))


def ci_safe_mode() -> bool:
    return os.environ.get("FLEET_CI_SAFE_MODE", "false").lower() == "true"


def probe(endpoint: str) -> dict:
    candidates = [
        endpoint.rstrip("/") + "/v1/models",
        endpoint.rstrip("/") + "/openai/v1/models",
        endpoint.rstrip("/") + "/health",
        endpoint.rstrip("/") + "/mcp",
    ]
    last_error = ""
    for url in candidates:
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return {
                    "returncode": 0,
                    "stdout": json.dumps({"url": url, "status": response.status}),
                    "stderr": "",
                }
        except urllib.error.HTTPError as exc:
            return {
                "returncode": 0,
                "stdout": json.dumps({"url": url, "status": exc.code}),
                "stderr": "",
            }
        except Exception as exc:
            last_error = str(exc)
    return {
        "returncode": 1,
        "stdout": "",
        "stderr": last_error or "foundry-local endpoint unavailable",
    }


def main():
    parser = argparse.ArgumentParser(description="Adapter for Foundry local provider")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    load_env_file()
    provider = load_provider()
    endpoint = resolve_endpoint(provider)
    result = probe(endpoint)
    if result["returncode"] != 0 and ci_safe_mode():
        result = {
            "returncode": 0,
            "stdout": json.dumps(
                {
                    "status": "skipped",
                    "reason": result["stderr"],
                    "mode": "ci-safe",
                    "endpoint": endpoint,
                }
            ),
            "stderr": "",
        }
    payload = {
        "agent": args.agent,
        "provider": "foundry-local",
        "endpoint": endpoint,
        "task": args.task,
        **result,
    }
    print(json.dumps(payload))
    raise SystemExit(result["returncode"])


if __name__ == "__main__":
    main()
