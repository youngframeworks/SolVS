#!/usr/bin/env bash
set -euo pipefail

required=(
  "config/fleet.json"
  "config/router.rules.json"
  "config/hooks.json"
  "config/mcp.servers.json"
  ".github/agents/solmanager.agent.md"
  "scripts/proposal_pack.py"
  "scripts/copilot_cli_adapter.py"
  "scripts/copilot_auth_check.py"
  "scripts/copilot_cli_doctor.py"
  "scripts/copilot_cli_install_check.sh"
  "scripts/foundry_local_adapter.py"
  "scripts/bootstrap_foundry_local.sh"
  "scripts/foundry_local_mock.py"
  "scripts/foundry_local_control.sh"
  "scripts/provider_badges.py"
  "scripts/provider_probe.py"
)

for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "missing: $f"
    exit 1
  fi
done

echo "validation ok"
