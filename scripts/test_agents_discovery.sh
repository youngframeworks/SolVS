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

# Look for a JSON agent field such as: "agent":"SolManager"
printf "%s" "$out" | python3 - <<'PY'
import sys, re
s = sys.stdin.read()
m = re.search(r'"agent"\s*:\s*"([^"]+)"', s)
if m and m.group(1) == 'SolManager':
  print('Found agent: SolManager')
  sys.exit(0)
else:
  print('Agent marker not found in output', file=sys.stderr)
  sys.exit(2)
PY

