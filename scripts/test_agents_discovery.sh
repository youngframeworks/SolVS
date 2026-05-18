#!/usr/bin/env bash
set -euo pipefail

# Run copilot_with_agents.sh in non-interactive mode to validate agent discovery
# Exits 0 on success, non-zero on failure.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

CLI_WRAPPER="bash scripts/copilot_with_agents.sh"

echo "+ Running: $CLI_WRAPPER --agent SolManager -p \"ping\""
if $CLI_WRAPPER --agent SolManager -p "ping"; then
  echo "Copilot wrapper returned success. Agent invocation likely discovered."
  exit 0
else
  echo "Copilot wrapper returned non-zero." >&2
  exit 1
fi
