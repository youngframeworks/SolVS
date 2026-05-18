---
# Local custom agents for Copilot CLI
---

## SolManager

The following are workspace-local agent definitions with richer metadata. Copilot CLI can discover these when run from the repository root.

```yaml
# Agent: SolManager
name: SolManager
description: Sol OS orchestrator for architecture review, drift scoring, self-heal, self-evolve, and autosync governance.
provider: foundry-local
model: qwen3.5-2b
tools:
	- planner
	- governance
	- mcp-router
	- self-heal
	- self-evolve
	- autopilot
	- research
permissions:
	allow_tools:
		- planner
		- shell
		- file
		- mcp
	allowed_paths:
		- config/**
		- scripts/**
		- runtime/**
	disallow_paths:
		- ~/.ssh/**
		- /etc/**
examples:
	- copilot: "bash scripts/copilot_with_agents.sh --agent SolManager -i \"review project architecture\""
	- copilot-autopilot: "bash scripts/copilot_with_agents.sh --agent SolManager --autopilot -i \"perform architecture review\""

# Agent: Fleet
name: Fleet
description: Fleet operator agent that routes tasks to the appropriate SolVS agents and providers, validates hooks, and assembles proposal packs.
provider: foundry-local
model: qwen3.5-2b
tools:
	- router
	- hooks-validator
	- provider-prober
	- proposal-builder
	- research
permissions:
	allow_tools:
		- router
		- shell
		- file
		- network
	allowed_paths:
		- config/**
		- scripts/**
		- runtime/**
	allow_network_domains:
		- 127.0.0.1
		- localhost
examples:
	- copilot: "bash scripts/copilot_with_agents.sh --agent Fleet -i \"route task: upgrade provider\""
	- copilot-research: "bash scripts/copilot_with_agents.sh --agent Fleet --mode research -i \"investigate provider performance\""

Notes:
- Tune `permissions` to align with governance requirements. These metadata entries are used by local agent runners and by the Copilot CLI when it exposes available tools/permissions to the session.

Place this file at the repository root so the Copilot CLI can discover local agent definitions when run from the workspace.

