#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
control_script="$root_dir/scripts/foundry_local_control.sh"
model_alias="${FOUNDRY_LOCAL_MODEL:-qwen3.5-2b}"

default_start_cmd="PYTHONPATH=\"$HOME/.local/lib/python3.13/site-packages:\$PYTHONPATH\" python3 \"$root_dir/scripts/foundry_local_sdk_launcher.py\" serve --model $model_alias"
export FOUNDRY_LOCAL_START_CMD="${FOUNDRY_LOCAL_START_CMD:-$default_start_cmd}"

echo "[foundry-quick-start] model=$model_alias"
echo "[foundry-quick-start] endpoint=${FOUNDRY_LOCAL_ENDPOINT:-http://127.0.0.1:5272}"

if ! bash "$control_script" start "$@"; then
  echo "[foundry-quick-start] bootstrap returned non-zero; probing endpoint for delayed readiness"
fi

python3 - "${FOUNDRY_LOCAL_ENDPOINT:-http://127.0.0.1:5272}" <<'PY'
import sys
import time
import urllib.request

base = sys.argv[1].rstrip('/')
url = base + '/v1/models'
for _ in range(60):
	try:
		with urllib.request.urlopen(url, timeout=2) as response:
			if response.status < 500:
				print(f"[foundry-quick-start] ready at {base}")
				raise SystemExit(0)
	except Exception:
		time.sleep(1)

print(f"[foundry-quick-start] endpoint not ready after wait: {base}")
raise SystemExit(1)
PY
