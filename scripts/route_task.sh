#!/usr/bin/env bash
set -euo pipefail

python3 scripts/route_task.py --task "${1:-route this task}"
