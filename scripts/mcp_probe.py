#!/usr/bin/env python3
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "mcp.servers.json"


def load_config():
    with CONFIG.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def accepted_http_statuses(server: dict) -> set[int]:
    configured = server.get("acceptedStatus")
    if isinstance(configured, list) and configured:
        return {int(code) for code in configured}
    accepted = set(range(200, 300))
    if bool(server.get("allow404", False)):
        accepted.add(404)
    return accepted


def probe_server(server: dict) -> dict:
    result = {
        "id": server["id"],
        "transport": server.get("transport", "unknown"),
        "status": "unknown",
        "detail": "",
    }
    transport = server.get("transport")
    if transport == "stdio":
        command = server.get("command", "")
        # If command contains args (e.g. 'npx'), pick the executable
        exe = command.split()[0] if isinstance(command, str) and command else command
        resolved = shutil.which(exe) if exe else None
        if resolved:
            result["status"] = "ok"
            result["detail"] = resolved
        else:
            # Provide actionable guidance for common missing tools
            if exe in ("npx", "npm"):
                hint = (
                    "npx not found in PATH. Install Node.js/npm or ensure npx is available. "
                    "Example (Debian/Ubuntu): 'sudo apt install -y nodejs npm' or 'sudo npm install -g npm'. "
                    "If using Node 18+, 'npx' is shipped with npm; ensure your PATH includes npm binaries."
                )
            elif exe:
                hint = f"command not found: {exe}. Ensure it is installed and available in PATH."
            else:
                hint = "no command configured for stdio transport"
            result["status"] = "error"
            result["detail"] = hint
        return result

    if transport == "http":
        url = server.get("url", "")
        accepted = accepted_http_statuses(server)
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status in accepted:
                    result["status"] = "ok"
                    result["detail"] = f"http {response.status}"
                else:
                    result["status"] = "error"
                    result["detail"] = f"http {response.status} (unexpected)"
        except urllib.error.HTTPError as exc:
            if exc.code in accepted:
                result["status"] = "ok"
                result["detail"] = f"http {exc.code}"
            else:
                result["status"] = "error"
                result["detail"] = f"http {exc.code} (unexpected)"
        except Exception as exc:
            result["status"] = "error"
            result["detail"] = str(exc)
        return result

    result["status"] = "error"
    result["detail"] = f"unsupported transport: {transport}"
    return result


def main():
    config = load_config()
    results = [probe_server(server) for server in config.get("servers", [])]
    print(json.dumps(results, indent=2))
    if any(result["status"] != "ok" for result in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
