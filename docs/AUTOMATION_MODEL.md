# Automation Model

This repository mirrors Copilot CLI routing primitives using explicit artifacts:

- Plans: generated per task under `runtime/plans/`.
- Fleet: declared in `config/fleet.json`.
- Tools: listed per agent and routed through MCP declarations.
- Hooks: declared in `config/hooks.json`.
- MCP: endpoints in `config/mcp.servers.json`.
- Self-heal loop: drift detection + proposal/apply gate.
- Self-evolve loop: rule optimization proposals + apply gate.

## Guardrails

- Proposal-first for healing and evolution.
- Apply mode needs explicit CLI flag and approval token.
- Every loop writes deterministic reports in `runtime/reports/`.
