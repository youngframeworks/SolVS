# .vscode (editor helpers)

This directory contains minimal editor helpers. The canonical, versioned
copies of agent, workflow, and policy documentation live under `docs/` and
`.github/agents/` in this repository.

Please edit the files under the following locations (single source of truth):

- `docs/vscode_agents/` — VS Code agent guidance and notes
- `docs/vscode_workflows/` — workflow examples and gates
- `docs/vscode_policies/` — governance and policy documentation
- `AGENTS.md` and `.github/agents/` — runtime agent metadata used by Copilot/Fleet

If you want local editor copies, create a symlink to the docs directory:

```bash
rm -rf .vscode/agents && ln -s "$(pwd)/docs/vscode_agents" .vscode/agents
```

Keep `.vscode/` minimal to avoid duplication; use the `docs/` area for
authoritative edits and CI-driven validation.
