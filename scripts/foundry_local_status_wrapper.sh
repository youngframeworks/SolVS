#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
endpoint="${FOUNDRY_LOCAL_ENDPOINT:-http://127.0.0.1:5272}"

bash "$root_dir/scripts/foundry_local_control.sh" status

python3 - "$endpoint" <<'PY'
import json
import sys
import urllib.request

endpoint = sys.argv[1].rstrip('/') + '/v1/models'
try:
    with urllib.request.urlopen(endpoint, timeout=5) as response:
        data = json.loads(response.read().decode('utf-8'))
except Exception as exc:
    print(f"[foundry-status] models unavailable: {exc}")
    raise SystemExit(1)

models = [m.get('id') for m in data.get('data', []) if isinstance(m, dict)]
print(f"[foundry-status] models={models}")
print(f"[foundry-status] qwen3.5-2b-present={any('qwen3.5-2b' in str(mid) for mid in models)}")
PY
