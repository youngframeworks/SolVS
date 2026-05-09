#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
endpoint="${FOUNDRY_LOCAL_ENDPOINT:-http://127.0.0.1:5272}"
endpoint_host="$(python3 - "$endpoint" <<'PY'
import sys
from urllib.parse import urlparse
parsed = urlparse(sys.argv[1])
print(parsed.hostname or '127.0.0.1')
PY
)"
endpoint_port="$(python3 - "$endpoint" <<'PY'
import sys
from urllib.parse import urlparse
parsed = urlparse(sys.argv[1])
print(parsed.port or 5272)
PY
)"
start_cmd="${FOUNDRY_LOCAL_START_CMD:-}"
pid_file="$root_dir/runtime/logs/foundry-local.pid"
log_file="$root_dir/runtime/logs/foundry-local.log"
meta_file="$root_dir/runtime/logs/foundry-local.meta.json"
use_mock=false
ensure_only=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mock)
      use_mock=true
      shift
      ;;
    --ensure)
      ensure_only=true
      shift
      ;;
    *)
      echo "unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

mkdir -p "$root_dir/runtime/logs"

check_ready() {
  python3 - "$endpoint" <<'PY'
import sys
import urllib.request
base = sys.argv[1].rstrip('/')
for suffix in ('/health', '/mcp'):
    try:
        with urllib.request.urlopen(base + suffix, timeout=2) as response:
            if response.status < 500:
                raise SystemExit(0)
    except Exception:
        pass
raise SystemExit(1)
PY
}

if check_ready; then
  echo "foundry-local ready at $endpoint"
  exit 0
fi

if [[ "$ensure_only" == true && -z "$start_cmd" && "$use_mock" != true ]]; then
  echo "foundry-local not ready and FOUNDRY_LOCAL_START_CMD is not set; rerun with --mock or export a start command" >&2
  exit 1
fi

if [[ -f "$pid_file" ]]; then
  old_pid="$(cat "$pid_file")"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "foundry-local bootstrap already running with pid $old_pid"
  else
    rm -f "$pid_file"
  fi
fi

if check_ready; then
  echo "foundry-local ready at $endpoint"
  exit 0
fi

if [[ "$use_mock" == true ]]; then
  nohup python3 "$root_dir/scripts/foundry_local_mock.py" --host "$endpoint_host" --port "$endpoint_port" >"$log_file" 2>&1 &
  echo $! >"$pid_file"
  python3 - "$meta_file" "$endpoint" "$pid_file" "$log_file" <<'PY'
import json
import pathlib
import sys
meta = pathlib.Path(sys.argv[1])
meta.write_text(json.dumps({
    "mode": "mock",
    "endpoint": sys.argv[2],
    "pidFile": sys.argv[3],
    "logFile": sys.argv[4],
}, indent=2) + "\n", encoding="utf-8")
PY
else
  nohup bash -lc "$start_cmd" >"$log_file" 2>&1 &
  echo $! >"$pid_file"
  python3 - "$meta_file" "$endpoint" "$start_cmd" "$pid_file" "$log_file" <<'PY'
import json
import pathlib
import sys
meta = pathlib.Path(sys.argv[1])
meta.write_text(json.dumps({
    "mode": "command",
    "endpoint": sys.argv[2],
    "startCommand": sys.argv[3],
    "pidFile": sys.argv[4],
    "logFile": sys.argv[5],
}, indent=2) + "\n", encoding="utf-8")
PY
fi

for _ in {1..15}; do
  if check_ready; then
    echo "foundry-local started at $endpoint"
    exit 0
  fi
  python3 - <<'PY'
import time
time.sleep(1)
PY
done

echo "foundry-local bootstrap started but endpoint did not become ready; see $log_file" >&2
exit 1
