#!/usr/bin/env bash
set -euo pipefail

# Simple prereq checks for SolVS development environment
# - node, npm, npx availability
# - Foundry local endpoint responsiveness (optional)

echo "SolVS prerequisite check"

check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "OK: $1"
  else
    echo "MISSING: $1"
  fi
}

check_cmd node
check_cmd npm
check_cmd npx

FOUNDRY_URL="${FOUNDRY_LOCAL_ENDPOINT:-http://127.0.0.1:5272}"

echo "Probing Foundry endpoint: $FOUNDRY_URL/v1/models"
if command -v curl >/dev/null 2>&1; then
  if curl -sS --max-time 5 "$FOUNDRY_URL/v1/models" >/dev/null 2>&1; then
    echo "OK: foundry models endpoint responded"
  else
    echo "WARN: foundry models endpoint did not respond as expected"
  fi
else
  echo "NOTE: curl not found; unable to probe Foundry endpoint"
fi

echo "Done."
