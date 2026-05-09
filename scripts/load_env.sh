#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  . ./.env
  set +a
elif [[ -f .env.example ]]; then
  set -a
  . ./.env.example
  set +a
fi
