#!/usr/bin/env bash
set -euo pipefail

service_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
service_file="$service_dir/solvs-foundry-qwen.service"

systemctl --user disable --now solvs-foundry-qwen.service 2>/dev/null || true
rm -f "$service_file"
systemctl --user daemon-reload

echo "Removed: $service_file"
