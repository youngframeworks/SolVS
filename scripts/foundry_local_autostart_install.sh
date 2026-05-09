#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
service_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
service_file="$service_dir/solvs-foundry-qwen.service"
model_alias="${FOUNDRY_LOCAL_MODEL:-qwen3.5-2b}"

mkdir -p "$service_dir"
cat >"$service_file" <<EOF
[Unit]
Description=SolVS Foundry Local (Qwen)
After=graphical-session.target network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$repo_root
Environment=FOUNDRY_LOCAL_MODEL=$model_alias
ExecStart=/bin/bash $repo_root/scripts/foundry_local_quick_start.sh
Restart=on-failure
RestartSec=15
TimeoutStartSec=180

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now solvs-foundry-qwen.service

echo "Installed and started: $service_file"
echo "Check status: systemctl --user status solvs-foundry-qwen.service"
echo "Disable: systemctl --user disable --now solvs-foundry-qwen.service"
