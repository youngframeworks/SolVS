#!/usr/bin/env bash
set -eu

endpoint="${FOUNDRY_LOCAL_ENDPOINT:-http://127.0.0.1:5272}"
echo "Foundry endpoint: $endpoint"

# Try basic probe of the endpoint
if ! output=$(curl -fsS "$endpoint" 2>/dev/null || true); then
  echo "ERROR: No response from $endpoint"
  exit 2
fi

# Print a short snippet for debugging
echo "--- response (first 20 lines) ---"
echo "$output" | head -n 20

# Check for the expected model name in the responses
if echo "$output" | grep -q "qwen3.5-2b"; then
  echo "OK: Model qwen3.5-2b available"
  exit 0
fi

# Try a models endpoint if available
if models_output=$(curl -fsS "$endpoint/models" 2>/dev/null || true); then
  if echo "$models_output" | grep -q "qwen3.5-2b"; then
    echo "OK: Model qwen3.5-2b available (from /models)"
    exit 0
  fi
fi

echo "ERROR: qwen3.5-2b not found in endpoint responses"
exit 3
