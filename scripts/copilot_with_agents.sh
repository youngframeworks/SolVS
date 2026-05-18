#!/usr/bin/env bash
set -euo pipefail

# Wrapper to run Copilot CLI using workspace-local agent definitions.
# Usage: ./scripts/copilot_with_agents.sh --agent SolManager -i "prompt"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Load .env if present
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

CLI="${COPILOT_CLI_BIN:-$(command -v copilot || echo "$HOME/.config/Code/User/globalStorage/github.copilot-chat/copilotCli/copilot")}" 

if [[ ! -x "$CLI" ]]; then
  echo "Copilot CLI not found or not executable: $CLI" >&2
  echo "Install the Copilot CLI or set COPILOT_CLI_BIN in .env" >&2
  exit 2
fi

# Ensure copilot reads local AGENTS.md by running in repo root; forward all args
exec "$CLI" "$@"
