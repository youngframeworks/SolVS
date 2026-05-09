#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pid_file="$root_dir/runtime/logs/foundry-local.pid"
log_file="$root_dir/runtime/logs/foundry-local.log"
meta_file="$root_dir/runtime/logs/foundry-local.meta.json"
endpoint="${FOUNDRY_LOCAL_ENDPOINT:-http://127.0.0.1:5272}"
endpoint_port="$(python3 - "$endpoint" <<'PY'
import sys
from urllib.parse import urlparse
parsed = urlparse(sys.argv[1])
print(parsed.port or 5272)
PY
)"

usage() {
  cat <<'TXT'
Usage:
  bash scripts/foundry_local_control.sh status
  bash scripts/foundry_local_control.sh stop
  bash scripts/foundry_local_control.sh start [--mock]
  bash scripts/foundry_local_control.sh restart [--mock]
  bash scripts/foundry_local_control.sh logs [--follow] [--lines N]
TXT
}

is_ready() {
  python3 - "$endpoint" <<'PY'
import sys
import urllib.request
base = sys.argv[1].rstrip('/')
for suffix in ('/v1/models', '/openai/v1/models', '/health', '/mcp'):
    try:
        with urllib.request.urlopen(base + suffix, timeout=2) as response:
            if response.status < 500:
                raise SystemExit(0)
    except Exception:
        pass
raise SystemExit(1)
PY
}

current_pid=""
if [[ -f "$pid_file" ]]; then
  current_pid="$(cat "$pid_file")"
fi

stop_process() {
  stopped_any=false

  if [[ -n "$current_pid" ]]; then
    if kill -0 "$current_pid" 2>/dev/null; then
      kill "$current_pid" || true
      echo "stopped foundry-local pid $current_pid"
      stopped_any=true
    else
      echo "foundry-local pid file existed but process was not running"
    fi
  fi

  # Fallback: stop any process currently listening on the configured endpoint port.
  extra_pids="$(lsof -ti TCP:"$endpoint_port" 2>/dev/null || true)"
  if [[ -n "$extra_pids" ]]; then
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill "$pid" 2>/dev/null || true
      echo "stopped foundry-local port listener pid $pid"
      stopped_any=true
    done <<< "$extra_pids"
  fi

  if [[ "$stopped_any" == false ]]; then
    echo "foundry-local not running"
  fi

  rm -f "$pid_file"
}

case "${1:-}" in
  status)
    ready=false
    if is_ready; then
      ready=true
    fi

    alive=false
    if [[ -n "$current_pid" ]] && kill -0 "$current_pid" 2>/dev/null; then
      alive=true
    fi

    python3 - "$meta_file" "$pid_file" "$log_file" "$endpoint" "$ready" "$alive" "$current_pid" <<'PY'
import json
import pathlib
import sys
meta_path = pathlib.Path(sys.argv[1])
pid_path = pathlib.Path(sys.argv[2])
log_path = pathlib.Path(sys.argv[3])
meta = {}
if meta_path.exists():
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        meta = {"raw": meta_path.read_text(encoding="utf-8")}
result = {
    "endpoint": sys.argv[4],
    "ready": sys.argv[5] == "true",
    "pidAlive": sys.argv[6] == "true",
    "pid": sys.argv[7] or None,
    "pidFile": str(pid_path),
    "logFile": str(log_path),
    "meta": meta,
}
print(json.dumps(result, indent=2))
PY
    ;;
  stop)
    stop_process
    ;;
  start)
    shift
    bash "$root_dir/scripts/bootstrap_foundry_local.sh" --ensure "$@"
    ;;
  restart)
    shift
    stop_process
    bash "$root_dir/scripts/bootstrap_foundry_local.sh" --ensure "$@"
    ;;
  logs)
    shift
    follow=false
    lines=80
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --follow)
          follow=true
          shift
          ;;
        --lines)
          if [[ $# -lt 2 ]]; then
            echo "--lines requires a numeric value" >&2
            exit 2
          fi
          lines="$2"
          shift 2
          ;;
        *)
          echo "unknown logs arg: $1" >&2
          exit 2
          ;;
      esac
    done

    if [[ ! -f "$log_file" ]]; then
      echo "no foundry-local log file at $log_file"
      exit 1
    fi

    if [[ "$follow" == true ]]; then
      tail -n "$lines" -f "$log_file"
    else
      tail -n "$lines" "$log_file"
    fi
    ;;
  *)
    usage
    exit 2
    ;;
esac
