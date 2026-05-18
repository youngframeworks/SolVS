# Running Copilot CLI in Offline Mode (Foundry Local)

This document explains how to run the Copilot CLI and the repository helpers in offline/local mode using Foundry Local (recommended) or another local provider.

Prerequisites

- Foundry Local or a compatible local provider running and reachable (default: `http://127.0.0.1:5272`).
- `python3` and the repository `requirements-dev.txt` for running tests and validation.

Environment variables

- `COPILOT_OFFLINE=true` — enable Copilot CLI offline behavior (local-only).  
- `COPILOT_PROVIDER_BASE_URL` — (optional) point to your Foundry Local endpoint (e.g. `http://127.0.0.1:5272`). If unset, some Copilot CLI discovery features will print a hint instead of JSON metadata.  
- `FOUNDRY_LOCAL_ENDPOINT` — an alias used by some scripts; set to the same value as `COPILOT_PROVIDER_BASE_URL` when appropriate.

Quick examples

1) Run the local model batch test (verifies model responds):

```bash
export COPILOT_OFFLINE=true
python3 scripts/test_qwen2b_batch.py
```

Expected: JSON-like responses for prompts. Some prompts may produce non-JSON outputs depending on model config.

2) Run the agent validator (ensure `AGENTS.md` matches `config/fleet.json`):

```bash
export COPILOT_OFFLINE=true
python3 scripts/validate_agents.py
```

3) Run the Copilot wrapper in offline mode (note: discovery JSON may not be emitted without `COPILOT_PROVIDER_BASE_URL`):

```bash
export COPILOT_OFFLINE=true
# If you have Foundry running, set provider URL for fuller behavior:
export COPILOT_PROVIDER_BASE_URL=http://127.0.0.1:5272

bash scripts/copilot_with_agents.sh --agent SolManager -p "ping"
```

If `COPILOT_PROVIDER_BASE_URL` is not set you may see:

```
Offline mode requires a local model provider. Set COPILOT_PROVIDER_BASE_URL to configure one.
```

Testing guidance

- For local runs (development), it's acceptable to set `COPILOT_OFFLINE=true` and rely on model tests (`scripts/test_qwen2b_batch.py`) and `scripts/validate_agents.py` for validation.
- For CI, configure `COPILOT_PROVIDER_BASE_URL` (and `COPILOT_BYOK_KEY` if applicable) as repository secrets so the discovery tests (`npm run test:agents`) run against a provider. See `docs/CI_SECRETS.md` for guidance.

Known behavior

- Copilot CLI discovery output (JSON agent marker) is only reliably emitted when the CLI can contact a configured provider. Offline hints are printed otherwise.
- You can relax `scripts/test_agents_discovery.sh` for local development, or set `COPILOT_PROVIDER_BASE_URL` for strict discovery checks.

Security

- Do not commit provider keys or tokens into source control. Use CI secrets for credentials and rotate keys regularly.
