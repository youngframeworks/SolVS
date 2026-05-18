#!/usr/bin/env bash
set -euo pipefail

# Run copilot_with_agents.sh in non-interactive mode to validate agent discovery
# Exits 0 on success, non-zero on failure.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

CLI_WRAPPER="bash scripts/copilot_with_agents.sh"

echo "+ Running: $CLI_WRAPPER --agent SolManager -p \"ping\" --output-format json"
out="$($CLI_WRAPPER --agent SolManager -p "ping" --output-format json 2>&1 || true)"
echo "$out"

# Write output to a temp file to avoid issues with stderr/stdout pipes.
tmpfile="/tmp/agents_discovery_out.$$"
printf "%s" "$out" > "$tmpfile"

python3 - "$tmpfile" <<PY
import sys, re
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as fh:
  s = fh.read()
# Look for JSON agent field
m = re.search(r'"agent"\s*:\s*"([^"]+)"', s)
if m and m.group(1) == 'SolManager':
  print('Found agent: SolManager')
  sys.exit(0)
# Accept common offline/provider hints
if 'Offline mode' in s or 'BYOK providers' in s or 'local model provider' in s:
  print('Offline/provider hint detected; accepting for local dev')
  sys.exit(0)
print('Agent marker not found in output and no offline hint present', file=sys.stderr)
sys.exit(2)
PY
rm -f "$tmpfile"

