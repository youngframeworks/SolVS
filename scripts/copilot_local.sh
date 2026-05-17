#!/usr/bin/env bash
set -euo pipefail

# Wrapper to run GitHub Copilot CLI using the Foundry Local model
# Forces FOUNDRY_LOCAL_MODEL to qwen3.5-2b by default (can be overridden)

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Load .env if present (does not error if missing)
if [ -f "$DIR/.env" ]; then
  # shellcheck disable=SC1090
  set -a
  # shellcheck source=/dev/null
  . "$DIR/.env"
  set +a
fi

: "${FOUNDRY_LOCAL_MODEL:=qwen3.5-2b}"
export FOUNDRY_LOCAL_MODEL

COPILOT_BIN="${COPILOT_CLI_BIN:-$(command -v copilot || true)}"
# Prefer foundry-local backend for interactive sessions
export COPILOT_CLI_BACKEND="foundry-local"
export COPILOT_CLI_BIN="$COPILOT_BIN"
if [ -z "$COPILOT_BIN" ]; then
  echo "Copilot CLI binary not found. Install it or set COPILOT_CLI_BIN." >&2
  exit 1
fi

exec "$COPILOT_BIN" "$@"
