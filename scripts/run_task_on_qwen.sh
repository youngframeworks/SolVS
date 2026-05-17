#!/usr/bin/env bash
set -euo pipefail
# Wrapper to run a single routing/task invocation with Foundry Qwen defaults.
# Usage: ./scripts/run_task_on_qwen.sh --task "..." [--execute]

# Move to repository root
DIR="$(cd "$(dirname "$0")" && pwd)/.."
cd "$DIR"

export FOUNDRY_LOCAL_MODEL="${FOUNDRY_LOCAL_MODEL:-qwen3.5-2b}"
export FOUNDRY_LOCAL_ENDPOINT="${FOUNDRY_LOCAL_ENDPOINT:-http://127.0.0.1:5272}"
export ALLOW_AUTONOMY="${ALLOW_AUTONOMY:-false}"

# Forward args to the route_task.py entrypoint which implements task routing
python3 scripts/route_task.py "$@"
