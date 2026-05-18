#!/usr/bin/env python3
"""
Validate AGENTS.md entries against config/fleet.json.

Requires: PyYAML (pip install pyyaml)

Checks:
- Each agent in AGENTS.md must reference a provider present in fleet.json providers
- If agent declares `model`, ensure provider in fleet.json has the same model
- If agent declares `tools`, ensure fleet.json has an agent entry with matching `id` and that tools overlap

Exit codes:
 0 on success, 1 on validation failures, 2 on missing dependency or parse errors
"""
import json
import os
import sys

try:
    import yaml
except Exception:
    print("PyYAML is required for this script. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_MD = os.path.join(REPO_ROOT, "AGENTS.md")
FLEET_JSON = os.path.join(REPO_ROOT, "config", "fleet.json")


def extract_yaml_blocks(md_text):
    blocks = []
    in_block = False
    cur = []
    for line in md_text.splitlines():
        if line.strip().startswith("```yaml"):
            in_block = True
            cur = []
            continue
        if in_block and line.strip().startswith("```"):
            in_block = False
            blocks.append("\n".join(cur))
            cur = []
            continue
        if in_block:
            cur.append(line)
    return blocks


def load_agents_from_md(path):
    with open(path, "r") as f:
        text = f.read()
    blocks = extract_yaml_blocks(text)
    agents = []
    for b in blocks:
        try:
            parsed = yaml.safe_load(b)
        except Exception as e:
            print(f"Failed to parse YAML block: {e}", file=sys.stderr)
            sys.exit(2)
        if not isinstance(parsed, dict):
            continue
        # The file may include multiple agent entries in one block; handle lists
        # If 'name' exists, treat as single agent
        if "name" in parsed:
            agents.append(parsed)
        else:
            # try to find nested agents
            for v in parsed.values():
                if isinstance(v, dict) and "name" in v:
                    agents.append(v)
    return agents


def load_fleet(path):
    with open(path, "r") as f:
        return json.load(f)


def find_agent_in_fleet(fleet, name):
    for a in fleet.get("agents", []):
        if a.get("id") == name or a.get("id", "").lower() == name.lower():
            return a
    return None


def main():
    if not os.path.exists(AGENTS_MD):
        print("AGENTS.md not found", file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(FLEET_JSON):
        print("config/fleet.json not found", file=sys.stderr)
        sys.exit(2)

    agents = load_agents_from_md(AGENTS_MD)
    fleet = load_fleet(FLEET_JSON)

    failures = []
    providers = fleet.get("providers", {})

    for a in agents:
        name = a.get("name")
        provider = a.get("provider")
        model = a.get("model")
        tools = a.get("tools") or []

        if not name:
            failures.append(("<unknown>", "missing name field in AGENTS.md entry"))
            continue

        if provider and provider not in providers:
            failures.append((name, f"provider '{provider}' not found in config/fleet.json"))
        else:
            if provider and model:
                fleet_model = providers.get(provider, {}).get("model")
                if fleet_model and fleet_model != model:
                    failures.append((name, f"model mismatch for provider '{provider}': AGENTS.md='{model}' vs fleet.json='{fleet_model}'"))

        fleet_agent = find_agent_in_fleet(fleet, name)
        if not fleet_agent:
            failures.append((name, "agent not declared in config/fleet.json agents list"))
        else:
            fleet_tools = fleet_agent.get("tools", [])
            # Check overlap
            missing_tools = [t for t in tools if t not in fleet_tools]
            if missing_tools:
                failures.append((name, f"tools declared in AGENTS.md not present in fleet.json agent entry: {missing_tools}"))

    if failures:
        print("Validation failures:")
        for name, reason in failures:
            print(f"- {name}: {reason}")
        sys.exit(1)

    print("AGENTS.md validation succeeded: entries align with config/fleet.json")
    sys.exit(0)


if __name__ == "__main__":
    main()
