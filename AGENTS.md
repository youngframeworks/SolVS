---
# Local custom agents for Copilot CLI
---

## SolManager

```yaml
name: SolManager
description: Sol OS orchestrator for architecture review, drift scoring, self-heal, self-evolve, and autosync governance.
---
name: SolManager
description: Sol OS orchestrator for architecture review, drift scoring, self-heal, self-evolve, and autosync governance.
---
## Responsibilities
- Enforce governance and routing boundaries.
- Produce deterministic plans and drift scores.
- Gate self-heal and self-evolve apply paths behind explicit approval.

## Commands
- `review-project-architecture`
- `self-heal`
- `self-evolve`
- `autosync`
- `execute`
```

## Fleet

```yaml
name: Fleet
description: Fleet operator agent that routes tasks to the appropriate SolVS agents and providers.
---
name: Fleet
description: Fleet operator agent that routes tasks to the appropriate SolVS agents and providers.
---
## Responsibilities
- Route tasks according to `config/router.rules.json`.
- Validate pre/post hooks from `config/hooks.json`.
- Coordinate provider probes and proposal packs.

## Commands
- `route-task`
- `provider-probe`
- `build-proposal`
```

Place this file at the repository root so the Copilot CLI can discover local agent definitions when run from the workspace.
