#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$ROOT_DIR/runtime/logs/foundry-local-sdk.log"
PID_FILE="$ROOT_DIR/runtime/logs/foundry-local-sdk.pid"
MODEL="${FOUNDRY_LOCAL_MODEL:-qwen3.5-2b}"

mkdir -p "$(dirname "$LOG")"

# Prefer SDK launcher if installed, otherwise fall back to mock server
if python3 -c "import importlib, sys
try:
    importlib.import_module('foundry_local_sdk')
    sys.exit(0)
except Exception:
    sys.exit(1)
"; then
  echo "Starting foundry-local SDK launcher (model=$MODEL)"
  nohup python3 "$ROOT_DIR/scripts/foundry_local_sdk_launcher.py" serve --model "$MODEL" >"$LOG" 2>&1 &
  echo $! >"$PID_FILE"
  echo "Started with PID $(cat $PID_FILE); logs: $LOG"
else
  echo "foundry_local_sdk not available; starting mock server instead"
  nohup python3 "$ROOT_DIR/scripts/foundry_local_mock.py" --host 127.0.0.1 --port 5272 >"$LOG" 2>&1 &
  echo $! >"$PID_FILE"
  echo "Mock server started with PID $(cat $PID_FILE); logs: $LOG"
fi
