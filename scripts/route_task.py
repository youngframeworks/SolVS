#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import shlex
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
RUNTIME = ROOT / "runtime"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def utc_timestamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def run_hook(command: str) -> dict:
    proc = subprocess.run(
        shlex.split(command),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def execute_hooks(hook_name: str, hooks: dict) -> list[dict]:
    results = []
    for command in hooks.get(hook_name, []):
        results.append(run_hook(command))
    return results


def set_execution_mode(execute: bool) -> str:
    mode = "execute" if execute else "proposal"
    os.environ["FLEET_EXECUTION_MODE"] = mode
    return mode


def build_agent_index(fleet: dict) -> dict:
    return {agent["id"]: agent for agent in fleet.get("agents", [])}


def run_provider_adapter(agent_id: str, provider_name: str, task: str, fleet: dict) -> dict:
    provider = fleet.get("providers", {}).get(provider_name, {})
    adapter = provider.get("adapter")
    if not adapter:
        return {
            "agent": agent_id,
            "provider": provider_name,
            "returncode": 1,
            "stdout": "",
            "stderr": f"no adapter configured for {provider_name}",
        }

    command = shlex.split(adapter) + ["--agent", agent_id, "--task", task]
    proc = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "agent": agent_id,
        "provider": provider_name,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def resolve_dispatch(route: list[str], fleet: dict, mcp_config: dict) -> list[dict]:
    agent_index = build_agent_index(fleet)
    servers = [server["id"] for server in mcp_config.get("servers", [])]
    dispatch = []
    for agent_id in route:
        agent = agent_index.get(agent_id, {})
        provider = agent.get("provider", fleet.get("defaultProvider", "copilot-cli"))
        transport_targets = list(servers)
        dispatch.append(
            {
                "agent": agent_id,
                "role": agent.get("role", "unknown"),
                "provider": provider,
                "tools": agent.get("tools", []),
                "mcpServers": transport_targets,
            }
        )
    return dispatch


def choose_route(task: str, rules: dict):
    task_l = task.lower()
    for rule in rules.get("rules", []):
        keywords = rule.get("matchAny", [])
        if any(k.lower() in task_l for k in keywords):
            return rule["id"], rule["route"]
    return "fallback", rules.get("fallbackRoute", ["SolOSRouter"])


def write_plan(task: str, rule_id: str, route: list[str]):
    timestamp = utc_timestamp()
    out = RUNTIME / "plans" / f"plan_{timestamp}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Plan {timestamp}",
        "",
        f"Task: {task}",
        f"Rule: {rule_id}",
        "Route:",
    ]
    lines.extend([f"- {agent}" for agent in route])
    lines.extend([
        "",
        "Execution Contract:",
        "- Step 1: classify intent",
        "- Step 2: assign agent chain",
        "- Step 3: run tools via MCP",
        "- Step 4: review and log",
    ])

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def write_run_summary(
    task: str,
    rule_id: str,
    route: list[str],
    execution_mode: str,
    dispatch: list[dict],
    pre_results: list[dict],
    post_results: list[dict],
    plan_file: Path,
    execution_results: list[dict],
) -> Path:
    timestamp = utc_timestamp()
    out = RUNTIME / "reports" / f"route_summary_{timestamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": timestamp,
        "task": task,
        "rule": rule_id,
        "executionMode": execution_mode,
        "route": route,
        "dispatch": dispatch,
        "execution": execution_results,
        "preRoute": pre_results,
        "postRoute": post_results,
        "planFile": str(plan_file.relative_to(ROOT)),
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser(description="Route a task to the SolVS agent fleet")
    parser.add_argument("--task", required=True, help="Incoming task text")
    parser.add_argument(
        "--write-summary",
        action="store_true",
        help="Write machine-readable route summary to runtime/reports",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Invoke provider adapters for the selected route",
    )
    args = parser.parse_args()

    hooks = load_json(CONFIG / "hooks.json").get("hooks", {})
    fleet = load_json(CONFIG / "fleet.json")
    mcp_config = load_json(CONFIG / "mcp.servers.json")
    rules = load_json(CONFIG / "router.rules.json")
    execution_mode = set_execution_mode(args.execute)
    pre_results = execute_hooks("preRoute", hooks)
    pre_failures = [result for result in pre_results if result["returncode"] != 0]
    if pre_failures:
        for failure in pre_failures:
            print("preRoute failed:", failure["command"])
            if failure["stderr"]:
                print(failure["stderr"])
        raise SystemExit(1)

    rule_id, route = choose_route(args.task, rules)
    dispatch = resolve_dispatch(route, fleet, mcp_config)
    plan_file = write_plan(args.task, rule_id, route)
    execution_results = []
    if args.execute:
        for item in dispatch:
            execution_results.append(
                run_provider_adapter(item["agent"], item["provider"], args.task, fleet)
            )
    post_results = execute_hooks("postRoute", hooks)
    summary_file = None
    if args.write_summary:
        summary_file = write_run_summary(
            args.task,
            rule_id,
            route,
            execution_mode,
            dispatch,
            pre_results,
            post_results,
            plan_file,
            execution_results,
        )

    print("route:", " -> ".join(route))
    print("plan:", plan_file)
    print("dispatch:", json.dumps(dispatch))
    if execution_results:
        print("execution:", json.dumps(execution_results))
        failures = [result for result in execution_results if result["returncode"] != 0]
        if failures:
            raise SystemExit(1)
    if summary_file is not None:
        print("summary:", summary_file)


if __name__ == "__main__":
    main()
