#!/usr/bin/env bash
set -euo pipefail

mkdir -p runtime/logs
printf '%s plan hook executed\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> runtime/logs/hooks.log
