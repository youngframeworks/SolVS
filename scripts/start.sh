#!/usr/bin/env bash
set -euo pipefail

# Start Foundry Local, wait for the HTTP endpoint, then run Copilot CLI via wrapper
# Usage: scripts/start_foundry_and_copilot.sh [--no-wait] [--timeout-secs N] [--] [copilot-args]

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

# Load .env if present
if [ -f "$DIR/.env" ]; then
  # shellcheck disable=SC1090
  . "$DIR/.env"
fi

NO_WAIT=false
TIMEOUT_SECS=${TIMEOUT_SECS:-60}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-wait) NO_WAIT=true; shift ;;
    --timeout-secs) TIMEOUT_SECS="$2"; shift 2 ;;
    --) shift; break ;;
    *) break ;;
  esac
done

FOUNDRY_ENDPOINT="${FOUNDRY_LOCAL_ENDPOINT:-http://127.0.0.1:5272}"

echo "[start_foundry_and_copilot] starting Foundry Local (endpoint=$FOUNDRY_ENDPOINT)"
bash scripts/foundry_local_quick_start.sh || true

if [ "$NO_WAIT" = false ]; then
  echo "[start_foundry_and_copilot] waiting up to ${TIMEOUT_SECS}s for Foundry endpoint to be ready..."
  SECONDS_PASSED=0
  until curl -sSf "$FOUNDRY_ENDPOINT/v1/models" >/dev/null 2>&1; do
    sleep 1
    SECONDS_PASSED=$((SECONDS_PASSED + 1))
    if [ "$SECONDS_PASSED" -ge "$TIMEOUT_SECS" ]; then
      echo "[start_foundry_and_copilot] timeout waiting for Foundry endpoint after ${TIMEOUT_SECS}s" >&2
      exit 1
    fi
  done
  echo "[start_foundry_and_copilot] Foundry endpoint is ready"
else
  echo "[start_foundry_and_copilot] not waiting for Foundry readiness (--no-wait)"
fi

# Run the copilot wrapper with any remaining args
COPILOT_WRAPPER="scripts/copilot_local.sh"
if [ ! -x "$COPILOT_WRAPPER" ]; then
  echo "Copilot wrapper $COPILOT_WRAPPER not found or not executable" >&2
  exit 1
fi

echo "[start_foundry_and_copilot] launching Copilot CLI via $COPILOT_WRAPPER"
# Query the adapter to show which backend/model will be used (best-effort)
if command -v python3 >/dev/null 2>&1; then
  set +e
  adapter_out=$(python3 scripts/copilot_cli_adapter.py --agent Startup --task "verify default provider model" 2>/dev/null || true)
  set -e
  if [ -n "$adapter_out" ]; then
    backend=$(printf '%s' "$adapter_out" | python3 -c "import sys,json; print(json.load(sys.stdin).get('backend',''))")
    model=$(printf '%s' "$adapter_out" | python3 -c "import sys,json; print(json.load(sys.stdin).get('model',''))")
    if [ -n "$backend" ] || [ -n "$model" ]; then
      echo "[start_foundry_and_copilot] adapter resolved backend=${backend:-unknown} model=${model:-unknown}"
    fi
  fi
fi

exec "$COPILOT_WRAPPER" "$@"
