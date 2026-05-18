# SolVS

**Autonomous multi-agent VS Code workspace** — Local-first AI orchestration with Foundry Local, MCP tools, and auto-healing/evolving loops. Production-ready agent framework with **zero GitHub rate limits**.

---

## 📋 Quick Navigation

| Purpose | Location |
|---|---|
| **Architecture & Design** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Deployment & Setup** | [docs/SETUP.md](docs/SETUP.md) |
| **Agent Contracts** | [.github/agents/](.github/agents/) |
| **Fleet Configuration** | [config/fleet.json](config/fleet.json) |

---

## ⚡ What's New: v3.3 (Local-First, Auto-Healing)

✅ **Foundry Local as Default**
- All agents (SolManager, Router, Implementer, Reviewer) use Qwen 3.5 2B locally
- **Zero GitHub Copilot Chat rate limits** — unlimited autonomy
- Fast local inference (800-1200ms per agent cycle)

✅ **Auto Self-Healing & Evolving**
- `autoSelfHeal: true` — Detects and proposes fixes automatically
- `autoSelfEvolve: true` — Continuously optimizes prompts and workflows
- No user intervention required (unless approval gate enabled)

✅ **Governance-First Autonomy**
- Human-gated execution: `ALLOW_AUTONOMY=true` required
- Atomic operations with full audit trail
- Reversible changes logged to OS_EVOLUTION_LOG.md

---

## 🚀 Quick Start (Local-First)

### Clone Repository

```bash
git clone https://github.com/youngframeworks/SolVS.git
cd SolVS/solvs-agent-fleet
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run Task (No Rate Limits)

```bash
# Plan a task (Foundry Local, no changes)
python3 scripts/route_task.py --task "analyze code quality"

# Execute with approval (all local)
ALLOW_AUTONOMY=true python3 scripts/route_task.py --task "analyze code quality" --execute

# Auto self-heal and evolve (continuous improvement)
ALLOW_AUTONOMY=true python3 scripts/autonomous_cycle.py --task "apply governance" --ticks 3
```

### Verify Setup

```bash
python3 scripts/provider_probe.py
# Expected: All providers green ✓ (all local)
```

# Run via wrapper (recommended)

```bash
# Ensures Qwen model and endpoint are used by default
bash scripts/run_task_on_qwen.sh --task "analyze code quality"
```

---

## 🏗️ Architecture (100% Local)

```
User Task
  │
  ▼
┌──────────────────────────────────────┐
│  SolOSRouter (Intent → Action)       │  ← Foundry Local (Qwen 3.5 2B)
└──────────────┬───────────────────────┘
               │
        ┌──────┼──────┐
        ▼      ▼      ▼
  ┌──────────────────────────────┐
  │ SolOSImplementer             │  ← Foundry Local
  │ SolOSReviewer                │  ← Foundry Local
  │ SolOSSysOps                  │  ← Foundry Local
  │ SolManager                   │  ← Foundry Local
  └─────────────┬────────────────┘
                │
                ▼
    Auto Self-Heal & Evolve
    (Continuous improvement loop)
```

---

## 📊 Provider Architecture (Local-Only)

| Provider | Role | Backend | Model | Rate Limit |
|---|---|---|---|---|
| **foundry-local** | All agents | HTTP localhost:5272 | Qwen 3.5 2B | ✅ None |
| **mcp** | Tools (optional) | Stdio | GitHub, Filesystem | ✅ Unlimited |
| **copilot-cli** | Fallback | Routes to Foundry Local | Qwen 3.5 2B | ✅ None |

**Key Advantage:** **Zero GitHub rate limits**. Unlimited local inference for autonomous cycles.

---

## 📁 Directory Structure

```
solvs-agent-fleet/
├── .github/agents/              # 5 agent specifications
├── .vscode/                     # VS Code tasks & policies
├── config/
│   ├── fleet.json              # DEFAULT: Foundry Local ⭐
│   ├── mcp.servers.json        # MCP tool declarations
│   ├── router.rules.json       # Routing heuristics
│   └── hooks.json              # Auto self-heal/evolve hooks
├── docs/                       # Architecture & setup guides
├── runtime/                    # Plans, reports, logs
├── scripts/                    # 30+ orchestration scripts
├── package.json
└── README.md (this file)
```

---

## 🎯 Common Tasks

### Plan a Task (Safe)
```bash
python3 scripts/route_task.py --task "implement feature X"
# Output: runtime/plans/task_routing_TIMESTAMP.json
```

### Run Task (Wrapper — ensures Qwen)
```bash
# Wrapper enforces FOUNDRY_LOCAL_MODEL=qwen3.5-2b and endpoint defaults
bash scripts/run_task_on_qwen.sh --task "implement feature X"
```

### Execute (Local + Auto-Heal — requires approval token)
```bash
# To execute provider actions you must provide an approval token and enable autonomy
AUTONOMY_APPROVAL_TOKEN=YOUR_TOKEN ALLOW_AUTONOMY=true python3 scripts/route_task.py --task "implement feature X" --execute
# Output: runtime/reports/execution_summary_TIMESTAMP.json
# Logged: OS_EVOLUTION_LOG.md
```

### Autonomous Cycle (Multi-Tick Improvement — provider execution requires token)
```bash
# Run autonomous cycle with provider execution; requires AUTONOMY_APPROVAL_TOKEN
AUTONOMY_APPROVAL_TOKEN=YOUR_TOKEN ALLOW_AUTONOMY=true python3 scripts/autonomous_cycle.py --task "apply policies" --ticks 3 --execute-providers
# Tick 1: Plan → Implement → Validate
# Tick 2: Auto-heal detected drift
# Tick 3: Auto-evolve prompts for improvements
```

### Self-Healing (Automatic)
```bash
# Auto self-heal can run during cycles; provider execution requires token
python3 scripts/self_heal.py --auto
# Detects and proposes fixes on each cycle
```

### Self-Evolving (Automatic)
```bash
# Auto self-evolve can run during cycles; provider execution requires token
python3 scripts/self_evolve.py --auto
# Continuously improves agent instructions and workflows
```

---

## 🛠️ VS Code Integration

Open this folder in VS Code. All tasks available in Command Palette:

**Execution:**
- **Fleet: Route Task** — Plan without execute
- **Fleet: Route And Execute** — Execute with gate (requires approval token when executing providers)
- **Fleet: Autonomous Cycle** — Multi-tick with auto-heal/evolve

**Diagnostics:**
- **Fleet: Provider Probe** — Check all providers (local only)
- **Fleet: MCP Probe** — Check MCP servers
- **Fleet: Foundry Status** — Check local model health
- **Fleet: Qwen Status** — Quick Foundry/Qwen health check (runs scripts/vscode_qwen_status.sh)

**VS Code Shortcut:**
- **Run task on Qwen Foundry** — uses scripts/run_task_on_qwen.sh (prompted input)

**Governance:**
- **Fleet: Self Heal (Auto)** — Auto-detect and propose fixes
- **Fleet: Self Evolve (Auto)** — Auto-improve prompts
- **Fleet: Validate** — Check readiness

---

## 🔐 Configuration (Local-First)

### config/fleet.json
```json
{
  "defaultProvider": "foundry-local",
  "autonomyMode": "enabled",
  "autoSelfHeal": true,
  "autoSelfEvolve": true,
  "governance": {
    "requireGate": "ALLOW_AUTONOMY",
    "atomicExecute": true,
    "auditLog": "OS_EVOLUTION_LOG.md"
  }
}
```

### Environment Variables
```bash
FOUNDRY_LOCAL_ENDPOINT=http://127.0.0.1:5272
ALLOW_AUTONOMY=true              # Enable execution & auto-heal
FLEET_EXECUTION_MODE=proposal|execute
```

---

## 🚀 Getting Started (5 minutes)

### 1. Clone (1 minute)
```bash
git clone https://github.com/youngframeworks/SolVS.git
cd SolVS/solvs-agent-fleet
```

### 2. Install (2 minutes)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Verify (1 minute)
```bash
python3 scripts/provider_probe.py  # All green ✓
```

### 4. First Task (varies)
```bash
# Plan (no changes)
python3 scripts/route_task.py --task "analyze workspace"

# Execute (local only)
ALLOW_AUTONOMY=true python3 scripts/route_task.py --task "analyze workspace" --execute
```

### 5. Auto-Improve (varies)
```bash
# Auto-heal + auto-evolve across 3 ticks
ALLOW_AUTONOMY=true python3 scripts/autonomous_cycle.py --task "governance audit" --ticks 3
```

---

## 🔐 Governance & Safety

### Human-Gated Execution
```bash
# ❌ Blocked (safe default)
python3 scripts/route_task.py --task "..." --execute

# ✅ Allowed (explicit approval with token)
AUTONOMY_APPROVAL_TOKEN=YOUR_TOKEN ALLOW_AUTONOMY=true python3 scripts/route_task.py --task "..." --execute
```

Important: Do NOT commit approval tokens into the repository. Store tokens in a secure secret manager or environment, and rotate frequently.

### Atomic & Reversible
- All changes: all-or-nothing
- Previous state: backed up
- Rollback: via git

### Fully Audited
- All changes → OS_EVOLUTION_LOG.md
- Auto-heal/evolve steps logged
- Full execution trail in runtime/reports/

---

## 🧬 What Changed (v3.2 → v3.3)

| Feature | v3.2 | v3.3 |
|---|---|---|
| **Default Provider** | copilot-cli | foundry-local ✅ |
| **Rate Limits** | GitHub quota (90% used) | None (unlimited local) ✅ |
| **SolManager** | copilot-cli | foundry-local ✅ |
| **Auto Self-Heal** | Manual | Enabled ✅ |
| **Auto Self-Evolve** | Manual | Enabled ✅ |
| **Governance** | Required gate | Required gate (same) ✓ |

---

## 💡 Why Foundry Local?

| Metric | GitHub Copilot Chat | Foundry Local (v3.3) |
|---|---|---|
| **Rate Limit** | ⚠️ Quota-limited | ✅ Unlimited |
| **Latency** | 500-800ms | 800-1200ms |
| **Cost** | $20/mo | Free ✅ |
| **Privacy** | Cloud | Local ✅ |
| **Auto Heal** | Manual | Automatic ✅ |
| **Auto Evolve** | Manual | Automatic ✅ |
| **Full Cycle** | ~2-3s | ~3-5s (all local) |

---

## 📚 Documentation

- **[docs/SETUP.md](docs/SETUP.md)** — Installation & Foundry Local bootstrap
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — System design deep-dive
- **[docs/AUTOMATION_MODEL.md](docs/AUTOMATION_MODEL.md)** — Autonomy & governance
- **[docs/LOCAL_BOOTSTRAP_AND_FALLBACKS.md](docs/LOCAL_BOOTSTRAP_AND_FALLBACKS.md)** — Foundry Local setup

---

## 🆘 Troubleshooting

### "Foundry Local not responding"
```bash
bash scripts/foundry_local_control.sh restart
```

### "ALLOW_AUTONOMY not set"
```bash
export ALLOW_AUTONOMY=true
```

### "Provider probe fails"
```bash
python3 scripts/provider_probe.py  # Detailed diagnostics
```

---

## 🤝 Contributing

1. Fork: `gh repo fork youngframeworks/SolVS --clone`
2. Branch: `git checkout -b feature/my-feature`
3. Test: `ALLOW_AUTONOMY=true python3 scripts/autonomous_cycle.py --task "test" --ticks 1`
4. PR: `git push origin feature/my-feature`

---

## 📝 License

MIT — See LICENSE file for details

---

## 🔗 Resources

- **GitHub:** https://github.com/youngframeworks/SolVS
- **Issues:** https://github.com/youngframeworks/SolVS/issues
- **Discussions:** https://github.com/youngframeworks/SolVS/discussions

---

**Status:** Production-Ready (v3.3 — Local-First, Auto-Healing)  
**Default Provider:** 🟢 Foundry Local (Qwen 3.5 2B)  
**Rate Limits:** ✅ None (100% local inference)  
**Last Updated:** 2026-05-17

## 📘 Usage Examples: Parallel Runner & CI

### Parallel Runner (SolManager + Fleet)
Run SolManager in `autopilot` and Fleet in `research` simultaneously and collect logs under `runtime/logs`:

```bash
# run both agents in parallel and capture logs
bash scripts/run_fleet_and_solmanager_parallel.sh -i "perform architecture review"
# or via npm
npm run copilot:parallel -- -i "perform architecture review"
```

Notes:
- Logs are written to `runtime/logs/parallel-<TIMESTAMP>/solmanager.log` and `fleet.log`.
- The runner forwards any flags you pass to the underlying wrappers.

### CI: GitHub Actions (what to expect)
The included workflow (`.github/workflows/ci.yml`) runs validation, linters, and tests on pushes and PRs. An optional `agents` job will run `npm run test:agents` only when the repository has the following secrets configured:

- `COPILOT_PROVIDER_BASE_URL` — base URL for the Copilot CLI provider (Foundry endpoint)
- `COPILOT_BYOK_KEY` — BYOK key or equivalent secret for provider access (if required)

To enable agent discovery tests in CI, add these secrets in your repository settings. The agents job will then execute the agent discovery and integration tests against your provider.

### Quick CI setup (secrets)
1. Go to your GitHub repo → Settings → Secrets → Actions.  
2. Add `COPILOT_PROVIDER_BASE_URL` (e.g., `http://foundry.local:5272`) and `COPILOT_BYOK_KEY` if needed.  
3. Open a PR or push to `main` to trigger the workflow.

If you'd like, I can add a small `docs/CI_SECRETS.md` explaining recommended secret scopes and a sample GitHub Actions secrets policy.

### Copilot CLI Offline Mode
See the full instructions in [docs/COPILOT_OFFLINE.md](docs/COPILOT_OFFLINE.md) for running the Copilot CLI and validation scripts in offline/local mode using Foundry Local.
