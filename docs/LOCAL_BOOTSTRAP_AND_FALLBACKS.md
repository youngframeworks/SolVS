# Local Bootstrap and Fallbacks

## Foundry-local bootstrap

Start or verify a local Foundry-compatible endpoint:

```bash
bash scripts/bootstrap_foundry_local.sh --ensure
```

Start the Qwen-backed Foundry Local runtime directly from the CLI:

```bash
FOUNDRY_LOCAL_START_CMD='PYTHONPATH="$HOME/.local/lib/python3.13/site-packages:$PYTHONPATH" python3 /home/young/SolVS/solvs-agent-fleet/scripts/foundry_local_sdk_launcher.py serve --model qwen3.5-2b' \
	bash scripts/foundry_local_quick_start.sh
```

Install a user-level autostart service for laptop login:

```bash
bash scripts/foundry_local_autostart_install.sh
```

Disable and remove the autostart service:

```bash
bash scripts/foundry_local_autostart_uninstall.sh
```

If you do not yet have a real Foundry local runtime command, use the mock server for local validation:

```bash
bash scripts/bootstrap_foundry_local.sh --ensure --mock
```

Set `FOUNDRY_LOCAL_START_CMD` to your real startup command when ready.

Manage runtime lifecycle:

```bash
bash scripts/foundry_local_control.sh status
bash scripts/foundry_local_control.sh stop
bash scripts/foundry_local_control.sh start --mock
bash scripts/foundry_local_control.sh restart --mock
bash scripts/foundry_local_control.sh logs --lines 120

### Cleaning cached models

After updating provider defaults you may want to remove unneeded model variants from the local cache. Use the helper script to keep only the models you need:

```bash
python3 scripts/clean_model_cache.py --keep qwen3.5-2b qwen2.5-coder-7b
```
```

## Copilot CLI auth check

Validate the standalone Copilot CLI and its non-interactive readiness:

```bash
python3 scripts/copilot_cli_doctor.py --format plain
```

Possible states:

- `ready`: standalone CLI works non-interactively
- `missing`: no standalone CLI was found
- `install-required`: wrapper exists but the real CLI is not installed
- `auth-required`: CLI exists but cannot complete non-interactive requests yet

Installer/check flow helper:

```bash
bash scripts/copilot_cli_install_check.sh
```

## CI-safe mode

Set these for unattended environments:

```bash
export FLEET_CI_SAFE_MODE=true
export COPILOT_PLAN_FALLBACK=true
```

Behavior:

- unavailable Foundry-local provider degrades to `skipped`
- unavailable Copilot CLI degrades to `plan-only`
- routing can continue and still generate reports and proposal artifacts

When needed, run autonomous cycles with provider execution under safe-mode policy:

```bash
FLEET_CI_SAFE_MODE=true COPILOT_PLAN_FALLBACK=true python3 scripts/autonomous_cycle.py --task "review security hardening" --ticks 3 --execute-providers
```

## Provider badges in proposal_latest.md

After proposal generation, provider status badges are inserted into `runtime/reports/proposal_latest.md` for PR visibility.

Manual refresh:

```bash
python3 scripts/provider_badges.py --proposal runtime/reports/proposal_latest.md
```
