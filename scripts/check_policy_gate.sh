#!/usr/bin/env bash
set -euo pipefail

mode="${FLEET_EXECUTION_MODE:-proposal}"
allow_autonomy="${ALLOW_AUTONOMY:-false}"

# Proposal-only actions are always allowed.
if [[ "$mode" == "proposal" ]]; then
  echo "policy gate: proposal mode allowed"
  exit 0
fi

# Execute/apply actions require explicit autonomy enablement.
if [[ "$allow_autonomy" != "true" ]]; then
  echo "policy gate: denied (mode=$mode, ALLOW_AUTONOMY=false)"
  exit 1
fi

echo "policy gate: allowed (mode=$mode, ALLOW_AUTONOMY=true)"
