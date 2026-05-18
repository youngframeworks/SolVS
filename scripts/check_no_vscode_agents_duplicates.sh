#!/usr/bin/env bash
set -euo pipefail
# Fail if there are regular files under .vscode/agents (we expect a symlink)
if [ -L ".vscode/agents" ]; then
  echo ".vscode/agents is a symlink -> OK"
  exit 0
fi

if [ -d ".vscode/agents" ]; then
  first_file="$(find .vscode/agents -type f -print -quit || true)"
  if [ -n "$first_file" ]; then
    echo "ERROR: Regular files found under .vscode/agents (duplicates)."
    echo "Please keep canonical copies under docs/vscode_agents and use a symlink in .vscode/agents."
    echo
    find .vscode/agents -type f -print
    exit 1
  fi
fi

echo "No regular files under .vscode/agents (ok)."
exit 0
