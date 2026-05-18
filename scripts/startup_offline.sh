#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="$root_dir/.venv"
req_file="$root_dir/requirements-dev.txt"

echo "Startup: offline mode helper"

if [ ! -d "$venv_dir" ]; then
  echo "Creating venv at $venv_dir"
  python3 -m venv "$venv_dir"
fi

echo "Activating venv"
# shellcheck disable=SC1090
source "$venv_dir/bin/activate"

if [ -f "$req_file" ]; then
  echo "Installing dev requirements"
  pip install --upgrade pip
  pip install -r "$req_file" || echo "pip install failed; continuing (you can install manually)"
else
  echo "No requirements-dev.txt found; skipping pip install"
fi

export COPILOT_OFFLINE=true
export COPILOT_PROVIDER_BASE_URL=${COPILOT_PROVIDER_BASE_URL:-http://127.0.0.1:5272}

echo "Using COPILOT_PROVIDER_BASE_URL=$COPILOT_PROVIDER_BASE_URL"

echo "Starting Foundry local (ensure)"
bash "$root_dir/scripts/foundry_local_control.sh" start --ensure || true

echo "Waiting for Foundry to become ready (timeout 60s)"
ready=false
for i in $(seq 1 30); do
  out=$(bash "$root_dir/scripts/foundry_local_control.sh" status || true)
  echo "$out" | sed -n '1,120p'
  if echo "$out" | grep -q '"ready": true'; then
    ready=true
    break
  fi
  sleep 2
done

if [ "$ready" != true ]; then
  echo "Foundry not ready after timeout; continuing anyway"
fi

echo "Running validation and model tests"
python3 "$root_dir/start.py" --validate --test --offline

echo "Launching Copilot CLI wrapper (offline mode)"
bash "$root_dir/scripts/copilot_with_agents.sh" --agent SolManager -p "ping" --output-format json || bash "$root_dir/scripts/copilot_with_agents.sh" --agent SolManager -p "ping"

echo "Startup sequence finished. Check runtime/logs for details."
