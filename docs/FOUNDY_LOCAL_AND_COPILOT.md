# Foundry Local and GitHub Copilot CLI

## Providers

The fleet uses multiple execution providers. Current routing defaults:

- `qwen-fast`: Foundry Local (qwen3.5-2b) — fast small tasks and short queries
- `qwen-coder`: Foundry Local (qwen2.5-coder-7b) — coding, generation, edits
- `copilot-pro`: Copilot Pro — complex planning, multi-step orchestration (fallback)
- `copilot-cli`: routes to Foundry Local by default and falls back to `copilot-pro` for complex tasks

## Local setup

1. Ensure `gh` with the Copilot extension is installed and authenticated.
2. Ensure your Foundry local runtime is reachable at `FOUNDRY_LOCAL_ENDPOINT`.
3. Copy `.env.example` values into your shell environment or a local env loader.

## Commands

Route and execute the selected provider chain:

```bash
python3 scripts/route_task.py --task "review security hardening" --execute --write-summary
```

Probe Foundry local directly:

```bash
python3 scripts/foundry_local_adapter.py --agent SolOSImplementer --task "health check"
```

Use Copilot CLI directly through the adapter:

```bash
python3 scripts/copilot_cli_adapter.py --agent SolManager --task "suggest a validation command"
```
