#!/usr/bin/env python3
"""MCP stdio server wrapping the foundry-local OpenAI-compatible API.

This exposes the SolVS fleet agents as MCP tools that VS Code Copilot Chat
can invoke directly. Run by VS Code as a stdio process via .vscode/mcp.json.

Protocol: JSON-RPC 2.0 over stdin/stdout (MCP spec 2024-11-05).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Ensure user-installed SDK is importable on Debian systems
_SDK_SITE = Path.home() / ".local" / "lib"
for _p in _SDK_SITE.glob("python*/site-packages"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ENDPOINT = os.environ.get("FOUNDRY_LOCAL_ENDPOINT", "http://127.0.0.1:5272")
MODEL = os.environ.get("FOUNDRY_LOCAL_MODEL", "qwen3.5-2b-generic-cpu")
ROOT = Path(__file__).resolve().parents[1]

TOOLS = [
    {
        "name": "sol_chat",
        "description": (
            "Send a message to the SolVS foundry-local model (qwen3.5-2b). "
            "Use for code generation, architecture review, self-heal plans, "
            "and general Sol OS reasoning tasks."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The prompt or task to send to the local model.",
                },
                "system": {
                    "type": "string",
                    "description": "Optional system prompt (defaults to Sol OS orchestrator role).",
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens to generate (default 512).",
                    "default": 512,
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "sol_route_task",
        "description": (
            "Route a Sol OS task to the appropriate fleet agent "
            "(SolManager, SolOSRouter, SolOSImplementer, SolOSSysOps, SolOSReviewer). "
            "Returns the agent selection and execution plan."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The task description to route.",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "If true, return routing plan only (no execution).",
                    "default": True,
                },
            },
            "required": ["task"],
        },
    },
    {
        "name": "sol_fleet_status",
        "description": "Return the current Sol OS fleet status: foundry-local endpoint, loaded model, and agent roster.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def _chat(message: str, system: str | None = None, max_tokens: int = 512) -> str:
    system_content = system or (
        "You are SolManager, the Sol OS Cloud Orchestrator. "
        "Be precise, structured, and operational."
    )
    payload = json.dumps(
        {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": message},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
    ).encode()
    req = urllib.request.Request(
        f"{ENDPOINT.rstrip('/')}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            return data["choices"][0]["message"]["content"]
    except urllib.error.URLError as exc:
        return f"[ERROR] foundry-local unreachable at {ENDPOINT}: {exc}"
    except Exception as exc:
        return f"[ERROR] {exc}"


def _route_task(task: str, dry_run: bool = True) -> str:
    import subprocess
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "route_task.py"), "--task", task]
        + (["--dry-run"] if dry_run else []),
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout.strip() or result.stderr.strip() or "(no output)"


def _fleet_status() -> str:
    meta_path = ROOT / "runtime" / "logs" / "foundry-local.meta.json"
    fleet_path = ROOT / "config" / "fleet.json"

    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    fleet = {}
    if fleet_path.exists():
        fleet = json.loads(fleet_path.read_text(encoding="utf-8"))

    # Probe liveness
    live = False
    try:
        with urllib.request.urlopen(f"{ENDPOINT.rstrip('/')}/v1/models", timeout=3) as r:
            models_data = json.loads(r.read())
            live = True
            loaded_models = [m["id"] for m in models_data.get("data", [])]
    except Exception:
        loaded_models = []

    agents = [a["id"] for a in fleet.get("agents", [])]

    return json.dumps(
        {
            "foundry_local": {
                "endpoint": meta.get("endpoint", ENDPOINT),
                "mode": meta.get("mode", "unknown"),
                "model_config": meta.get("model", MODEL),
                "loaded_models": loaded_models,
                "live": live,
            },
            "fleet_agents": agents,
            "default_provider": fleet.get("defaultProvider", "unknown"),
        },
        indent=2,
    )


def _call_tool(name: str, arguments: dict) -> str:
    if name == "sol_chat":
        return _chat(
            message=arguments["message"],
            system=arguments.get("system"),
            max_tokens=arguments.get("max_tokens", 512),
        )
    if name == "sol_route_task":
        return _route_task(
            task=arguments["task"],
            dry_run=arguments.get("dry_run", True),
        )
    if name == "sol_fleet_status":
        return _fleet_status()
    return f"[ERROR] unknown tool: {name}"


def _send(obj: dict) -> None:
    line = json.dumps(obj, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _error(req_id, code: int, message: str) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def main() -> None:
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            msg = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "solvs-foundry-fleet", "version": "1.0.0"},
                    },
                }
            )

        elif method == "notifications/initialized":
            # No response needed for notifications
            pass

        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            try:
                output = _call_tool(tool_name, arguments)
                _send(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": output}],
                            "isError": output.startswith("[ERROR]"),
                        },
                    }
                )
            except Exception as exc:
                _error(req_id, -32603, str(exc))

        elif method == "ping":
            _send({"jsonrpc": "2.0", "id": req_id, "result": {}})

        elif req_id is not None:
            _error(req_id, -32601, f"Method not found: {method}")


if __name__ == "__main__":
    main()
