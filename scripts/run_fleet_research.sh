#!/usr/bin/env bash
set -euo pipefail

# Run Fleet in research mode via copilot wrapper
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a; source .env; set +a
fi

exec bash scripts/copilot_with_agents.sh --agent Fleet --mode research "$@"
