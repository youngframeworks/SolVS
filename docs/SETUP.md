# SolVS Setup & Installation Guide

Complete guide to clone, install, and run SolVS Agent Fleet.

---

## 🔗 Cloning the Repository

### Clone SolVS

```bash
git clone https://github.com/youngframeworks/SolVS.git
cd SolVS/solvs-agent-fleet
```

### GitHub URL

- **HTTPS:** `https://github.com/youngframeworks/SolVS.git`
- **SSH:** `git@github.com:youngframeworks/SolVS.git`
- **GitHub CLI:** `gh repo clone youngframeworks/SolVS`

---

## 📦 Installation

### Requirements

- **Python:** 3.10+
- **Git:** 2.40+
- **Node.js:** 18+ (for MCP tools)
- **VS Code:** 1.85+ (optional, for IDE integration)

### 1. Create Virtual Environment

```bash
cd SolVS/solvs-agent-fleet
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

**Key environment variables:**

```bash
# Foundry Local (local model server)
FOUNDRY_LOCAL_ENDPOINT=http://127.0.0.1:5272

# Copilot CLI (optional, now routed through Foundry Local)
# COPILOT_CLI_BIN=/path/to/copilot

# Governance gate (required for execute mode)
ALLOW_AUTONOMY=false  # Set to 'true' to enable execution

# GitHub token (for PR workflows)
GITHUB_TOKEN=github_pat_...

# Execution mode
FLEET_EXECUTION_MODE=proposal  # or 'execute'
```

### 4. Verify Installation

```bash
# Check provider readiness
python3 scripts/provider_probe.py

# Check MCP servers
python3 scripts/mcp_probe.py

# Check Copilot CLI status
python3 scripts/copilot_cli_doctor.py --format plain
```

---

## 🚀 Quick Start

### 1. Plan a Task (Proposal Mode)

```bash
python3 scripts/route_task.py --task "analyze code quality"
```

Output will be saved to `runtime/plans/`.

### 2. Execute with Approval

```bash
ALLOW_AUTONOMY=true python3 scripts/route_task.py \
  --task "analyze code quality" \
  --execute --write-summary
```

Output will be saved to `runtime/reports/`.

### 3. Run Autonomous Cycle

```bash
ALLOW_AUTONOMY=true python3 scripts/autonomous_cycle.py \
  --task "apply governance policies" \
  --ticks 3
```

Runs 3 iterations of: plan → propose → review → execute.

---

## 🛠️ Foundry Local Setup (Local Model Serving)

### Why Foundry Local?

SolVS uses Foundry Local to run Qwen 3.5 2B locally for fast, deterministic inference without relying on GitHub Copilot CLI.

### Install Foundry Local

```bash
# Automatic bootstrap via VS Code task:
# - Command Palette: "Fleet: Bootstrap Foundry Local"

# Or manual installation:
bash scripts/foundry_local_quick_start.sh
```

### Check Status

```bash
bash scripts/foundry_local_control.sh status
```

Expected output:
```
✓ Qwen 3.5 2B running on http://127.0.0.1:5272
✓ Health check: 200 OK
```

### Start/Stop Foundry Local

```bash
# Start
bash scripts/foundry_local_control.sh restart

# Stop
bash scripts/foundry_local_control.sh stop

# View logs
bash scripts/foundry_local_control.sh logs --lines 50
```

---

## 🔑 Copilot CLI Authentication

### Option 1: Via GitHub CLI (Recommended)

```bash
# Install GitHub CLI if needed
brew install gh  # macOS
# or
sudo apt install gh  # Linux

# Login to GitHub
gh auth login

# Copilot CLI will automatically use GitHub CLI credentials
python3 scripts/copilot_cli_doctor.py --format plain
```

### Option 2: Device Flow (Interactive)

```bash
copilot login
# Browser will open for authentication
# Confirm device code in GitHub
```

### Option 3: Token via Environment

```bash
export COPILOT_CLI_TOKEN=github_pat_XXXXX
```

**⚠️ Important:** Use modern GitHub PAT format (`github_pat_` or `gho_`). Classic `ghp_` tokens are rejected.

### Verify Authentication

```bash
python3 scripts/copilot_cli_doctor.py --format plain
```

Expected output:
```
COPILOT_STATUS=ready
backend=foundry-local
model=qwen3.5-2b
```

---

## 🖥️ VS Code Integration

### 1. Open Workspace

```bash
code .
```

### 2. Install Recommended Extensions

VS Code will suggest:
- GitHub Copilot
- GitHub Copilot Chat
- Pylance
- Python

### 3. Run Tasks

Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) and search:

- `Fleet:` (lists all SolVS tasks)
- `Fleet: Route Task`
- `Fleet: Route And Execute`
- `Fleet: Autonomous Cycle`

### 4. Custom Agent Specs

Agent specs are in `.github/agents/`:

- `solmanager.agent.md` — Orchestration
- `solosrouter.agent.md` — Routing
- `solosimplementer.agent.md` — Code generation
- `solosreviewer.agent.md` — Validation
- `solossysops.agent.md` — Diagnostics

Edit these files to customize agent behavior.

---

## 📋 MCP Configuration

### Add a New MCP Server

Edit `config/mcp.servers.json`:

```json
{
  "my-custom-tool": {
    "transport": "stdio",
    "command": "npx",
    "args": ["@modelcontextprotocol/server-my-tool"]
  }
}
```

### Verify MCP Server

```bash
python3 scripts/mcp_probe.py
```

---

## 🧪 Testing & Validation

### Run All Checks

```bash
bash scripts/validate.sh
```

Checks:
- Python syntax
- Config validity
- Provider readiness
- MCP connectivity

### Test with Mock Data

```bash
FLEET_CI_SAFE_MODE=true python3 scripts/autonomous_cycle.py \
  --task "test task" \
  --ticks 1
```

---

## 🐛 Troubleshooting

### "ALLOW_AUTONOMY not set"

```bash
# Solution
export ALLOW_AUTONOMY=true
ALLOW_AUTONOMY=true python3 scripts/route_task.py --task "..." --execute
```

### "Foundry Local not responding"

```bash
# Check status
bash scripts/foundry_local_control.sh status

# Restart
bash scripts/foundry_local_control.sh restart

# Check logs
bash scripts/foundry_local_control.sh logs --lines 100
```

### "Provider probe fails"

```bash
# Full diagnostics
python3 scripts/provider_probe.py

# Check individual providers
python3 scripts/copilot_cli_doctor.py --format plain
python3 scripts/mcp_probe.py
```

### "MCP server not found"

```bash
# Verify Node.js is installed
node --version

# Re-probe MCP
python3 scripts/mcp_probe.py

# Check config/mcp.servers.json for correct paths
cat config/mcp.servers.json
```

### "ModuleNotFoundError: No module named 'X'"

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify virtual environment is activated
source .venv/bin/activate
```

---

## 🔄 Updating SolVS

### Pull Latest Changes

```bash
cd SolVS/solvs-agent-fleet
git pull origin main
```

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Check for Breaking Changes

```bash
git log --oneline -10  # Review recent commits
```

---

## 📚 Next Steps

1. **Read Architecture:** [docs/ARCHITECTURE.md](ARCHITECTURE.md)
2. **Explore Examples:** Check `runtime/reports/` for sample outputs
3. **Customize Agents:** Edit `.github/agents/*.agent.md`
4. **Run Tasks:** `python3 scripts/route_task.py --task "your task"`

---

## 🆘 Getting Help

- **Issues:** https://github.com/youngframeworks/SolVS/issues
- **Discussions:** https://github.com/youngframeworks/SolVS/discussions
- **Email:** frameworks@youngframeworks.ai

---

**Last Updated:** 2026-05-10  
**Status:** Production-Ready (v3.2+)
