# Copilot instructions — SolVS

Purpose: Help future Copilot sessions understand how to build, test, and navigate this repository.

1) Build, test, and lint (what exists here)

- Setup (venv + deps):
  - python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

- Run project tasks (npm wrapper):
  - npm run fleet:route            # plan routing check
  - npm run fleet:cycle            # run 3-tick autonomous cycle (no execute)
  - npm run fleet:cycle:execute    # cycle with execution flags
  - npm run fleet:provider-probe   # check providers
  - npm run fleet:foundry-status   # foundry local status
  - npm run fleet:validate         # run repository validation (scripts/validate.sh)

- Single-test / ad-hoc scripts:
  - python3 test_foundry.py        # runs the foundry demo script
  - python3 test_script.py         # streaming demo script
  - python3 scripts/route_task.py --task "..." [--execute]  # run a single routing job

- Linting / format: No dedicated lint scripts found in package.json. Use your preferred tools (black, flake8, mypy) locally; validation is available via `npm run fleet:validate`.

2) High-level architecture (big picture)

- This repo is a local-first, autonomous multi-agent fleet (SolOSRouter, SolManager, Implementer, Reviewer, SysOps) orchestrating work via scripts/ and config/
- Default provider is foundry-local (see config/fleet.json). Provider definitions and MCP server entries live in config/mcp.servers.json — add a 'foundry-local' entry that points to your local Foundry endpoint. Environment variable FOUNDRY_LOCAL_ENDPOINT may override the endpoint.
- Core runtime artifacts live under runtime/ (plans, reports, logs). Fleet configuration lives in config/ (fleet.json, mcp.servers.json, router.rules.json).
- Orchestration is script-driven (scripts/). Key entry points are scripts/route_task.py, scripts/autonomous_cycle.py, and scripts/provider_probe.py.

- MCP server (quick action):
  - Add a Foundry Local entry to config/mcp.servers.json. Example single-line entry:
    {"name":"foundry-local","type":"foundry","endpoint":"http://localhost:7860","auth":{}}
  - Verify connectivity after adding the entry with either:
    - npm run fleet:provider-probe
    - python3 scripts/provider_probe.py
  - Once connectivity is successful, the provider will be available to fleet scripts that reference the 'foundry-local' provider name.
- Governance gating: ALLOW_AUTONOMY environment variable controls whether autonomous execution is permitted; see README for audit/logging locations (OS_EVOLUTION_LOG.md).

3) Key conventions (project-specific patterns)

- Use npm script wrappers (package.json) to run common tasks; they call Python scripts to keep commands consistent across environments.
- config/fleet.json contains defaults (defaultProvider, autoSelfHeal, autoSelfEvolve, governance). Prefer editing this file for fleet-wide changes.
- runtime/ is the writable workspace for generated plans, reports, and execution summaries. Do not commit runtime/* files.
- Use environment gating for any executing script that can change code or infra: ALLOW_AUTONOMY must be set to enable execute behaviors.
- Agent specs and fleet-level agent manifests are stored under .github/agents/ — Copilot sessions that manage agents should inspect this folder for agent metadata.
- Single-purpose demos and tests are plain Python scripts (no pytest harness required). Run them directly with python3 when debugging.

4) Where to find more detail

- docs/SETUP.md and docs/ARCHITECTURE.md contain deeper onboarding and architecture diagrams. README.md has quick-start and common commands.

5) AI-assistant / tooling configs

- No CLAUDE.md, .cursorrules, AGENTS.md, .windsurfrules, AIDER_CONVENTIONS.md, or other assistant rule files were found in the repository root.

---

If this file should incorporate more specific scripts, a CI matrix, or explicit lint/test commands (e.g., adding pytest or black invocations), say which tools to include and Copilot will add them.

== Actionable references (use when writing prompts or making edits) ==

- Files to consult for implementation or prompts:
  - scripts/route_task.py           — router (single task entrypoint)
  - scripts/autonomous_cycle.py     — plan → propose → review → execute loop
  - scripts/provider_probe.py       — provider readiness checks
  - scripts/mcp_probe.py            — MCP server verification
  - scripts/copilot_cli_adapter.py   — how copilot-style prompts are routed
  - config/fleet.json               — fleet defaults (defaultProvider, autoSelfHeal, autoSelfEvolve)
  - config/mcp.servers.json         — MCP tool/server declarations
  - .github/agents/*.agent.md       — agent system prompts and contracts
  - OS_EVOLUTION_LOG.md             — audit trail for applied changes

== Safety & governance reminders for Copilot sessions ==

- Never run execute-mode commands without explicit user confirmation and ALLOW_AUTONOMY=true. If asked to execute, require the user to confirm the gate.
- Default to proposal mode for suggested changes; include exact file paths and diffs to reproduce.
- When suggesting MCP servers or new providers, include verification steps (e.g., run `python3 scripts/mcp_probe.py`).

== MCP server note ==

- MCP servers are declared in config/mcp.servers.json. Common entries in this repo: filesystem, github, foundry-local.
- To add a server: edit config/mcp.servers.json, then run `python3 scripts/mcp_probe.py` to verify.

== Merge guidance ==

- A repository-level copilot-instructions.md already exists at project root. If updating either file, merge important lines so Copilot sessions find consistent guidance.

---

If you'd like, Copilot can add example lint/test CI steps or expand the "Files to consult" list. Let me know which area to prioritize.

== Running tasks on Qwen (Foundry local) ==

- Copilot CLI: use scripts/run_task_on_qwen.sh --task "..." to ensure FOUNDRY_LOCAL_MODEL is qwen3.5-2b and the Foundry endpoint is used.

- VSCode: a provided .vscode/tasks.json adds a "Run task on Qwen Foundry" task which prompts for a task name and runs the wrapper script. This routes the job through SolManager/Fleet using the configured default provider.

- Autonomy: ALLOW_AUTONOMY defaults to false. To enable autonomous apply you must explicitly set ALLOW_AUTONOMY=true and follow the governance approval/token flow. Do NOT enable without explicit approval and auditing in OS_EVOLUTION_LOG.md.


