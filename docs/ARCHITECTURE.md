# SolVS Architecture Deep-Dive

Complete technical architecture for the SolVS Agent Fleet multi-agent orchestration system.

---

## 🏛️ System Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                   Input Task (User)                          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│          Deterministic Router (route_task.py)               │
│  - Intent classification                                    │
│  - Agent selection                                          │
│  - Execution planning                                       │
└──────────────┬───────────────┬──────────────┬───────────────┘
               │               │              │
        ┌──────▼────┐  ┌────────▼──┐  ┌──────▼─────┐
        │SolOSRouter│  │SolOSImp   │  │SolOSReview │
        │           │  │lementer   │  │            │
        │Intent→    │  │Code→      │  │Validate→   │
        │Classify   │  │Generate   │  │CheckPolicy │
        └──────┬────┘  └────────┬──┘  └──────┬─────┘
               │                │             │
        ┌──────▼────────────────▼─────────────▼──────┐
        │  SolOSSysOps (Diagnostics & Health)       │
        │  - Run health checks                      │
        │  - Collect metrics                        │
        │  - Report status                          │
        └──────┬──────────────────────────────────┬──┘
               │                                  │
               └──────────────┬───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            SolManager (Aggregation & Governance)             │
│  - Collect results from all agents                          │
│  - Apply governance policies                                │
│  - Generate artifacts (proposals, reports)                  │
│  - Enforce execution gates                                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────┐
         │ Output: Proposal or Execution      │
         │ - Plans written to runtime/plans/  │
         │ - Reports written to runtime/      │
         │ - Logs captured to runtime/logs/   │
         └────────────────────────────────────┘
```

---

## 🔀 Provider Architecture

### Three-Provider Model

**1. copilot-cli Provider**
- **Role:** Intent routing, code generation, validation
- **Backend:** Foundry Local (HTTP) with Qwen 3.5 2B model
- **Implementation:** `scripts/copilot_cli_adapter.py`
- **Features:**
  - Automatic backend routing (no Copilot CLI binary required)
  - Token sanitization (modern PAT format only)
  - Execute mode with `--allow-all` permission flag
  - Deterministic output (local inference)

**2. foundry-local Provider**
- **Role:** Local model inference
- **Backend:** HTTP endpoint (default: http://127.0.0.1:5272)
- **Implementation:** `scripts/foundry_local_adapter.py`
- **Features:**
  - Qwen 3.5 2B model serving
  - Low latency (local inference)
  - Health check endpoint
  - Lifecycle management (start/stop/restart)

**3. mcp Provider**
- **Role:** Tool access (filesystem, GitHub, custom)
- **Backend:** Stdio protocol (Python processes)
- **Implementation:** `scripts/mcp_probe.py`
- **Declared in:** `config/mcp.servers.json`
- **Available Tools:**
  - Filesystem: `read_file`, `write_file`, `list_dir`
  - GitHub: `create_pull_request`, `list_issues`, `get_pr`
  - Custom tools via extended MCP servers

### Provider Routing Flow

```
Agent Request
     │
     ▼
┌─────────────────────────────────────┐
│ copilot_cli_adapter.py              │
│ - Check backend setting             │
│ - Route to Foundry Local            │
└─────────────────────────────────────┘
     │
     ├─→ backend=foundry-local
     │   └─→ foundry_local_adapter.py
     │       └─→ HTTP POST /v1/chat/completions
     │           └─→ Qwen 3.5 2B (27B quantized)
     │
     └─→ backend=copilot (legacy)
         └─→ GitHub Copilot CLI binary
             └─→ GitHub Cloud (slow, interactive)
```

---

## 👥 Agent Specifications

### 1. SolManager (Orchestration)

**File:** `.github/agents/solmanager.agent.md`

**Purpose:** Orchestration, governance, result aggregation

**Responsibilities:**
- Collect results from router, implementer, reviewer, sysops
- Apply governance policies
- Generate proposal and execution reports
- Enforce ALLOW_AUTONOMY gate
- Maintain evolution logs

**Provider:** copilot-cli (Qwen 3.5 2B)

**Input Template:**
```markdown
Task: [user task]

Context:
- Router intent: [classified intent]
- Implementer plan: [generated code changes]
- Reviewer validation: [pass/fail with comments]
- SysOps health: [system status]

Governance Rules:
- Only apply changes if all validations pass
- Log all changes to OS_EVOLUTION_LOG.md
- Ensure atomicity and reversibility
```

**Output:**
- Proposal markdown (if proposal mode)
- Execution summary (if execute mode)
- Governance enforcement report

---

### 2. SolOSRouter (Intent Classification)

**File:** `.github/agents/solosrouter.agent.md`

**Purpose:** Intent classification and agent routing

**Responsibilities:**
- Classify user task intent
- Select appropriate agents
- Route to implementer/reviewer/sysops
- Generate routing rationale

**Provider:** copilot-cli (Qwen 3.5 2B)

**Classification Examples:**
- "implement feature X" → Implementer
- "validate config" → Reviewer
- "check health" → SysOps
- "mixed task" → Multiple agents

---

### 3. SolOSImplementer (Code Generation)

**File:** `.github/agents/solosimplementer.agent.md`

**Purpose:** Code generation and changes

**Responsibilities:**
- Generate implementation plans
- Create code patches
- Document changes
- Support multiple languages

**Provider:** copilot-cli (Qwen 3.5 2B, or Qwen Coder 7B for complex tasks)

**Output:**
- Unified diff format
- Implementation rationale
- Testing suggestions

---

### 4. SolOSReviewer (Validation)

**File:** `.github/agents/solosreviewer.agent.md`

**Purpose:** Code review and policy validation

**Responsibilities:**
- Review proposed changes
- Check governance compliance
- Validate security policies
- Sign-off or suggest improvements

**Provider:** copilot-cli (Qwen 3.5 2B or Gemma 4E4B for lightweight review)

**Validation Checks:**
- Syntax correctness
- Policy alignment
- Security best practices
- Performance impact

---

### 5. SolOSSysOps (Diagnostics)

**File:** `.github/agents/solossysops.agent.md`

**Purpose:** System diagnostics and health

**Responsibilities:**
- Run health checks
- Collect system metrics
- Report provider status
- Monitor resource usage

**Provider:** Foundry Local HTTP (direct health check)

**Health Metrics:**
- Provider availability (copilot-cli, foundry-local, mcp)
- MCP server connectivity
- System resources (CPU, memory, disk)
- Network latency

---

## 🔄 Execution Modes

### Proposal Mode (Default)

```
User Input
    │
    ▼
Route Task
    │
    ├─→ SolOSRouter (classify intent)
    ├─→ SolOSImplementer (generate plan)
    ├─→ SolOSReviewer (validate)
    └─→ SolManager (aggregate)
              │
              ▼
         Proposal Report
      (runtime/reports/)
              │
              ▼
        Human Reviews
    [no changes applied]
```

**Output Files:**
- `runtime/reports/proposal_latest.md`
- `runtime/plans/task_routing_TIMESTAMP.json`

### Execute Mode (Gated)

```
User Input + ALLOW_AUTONOMY=true
    │
    ▼
Policy Gate (check_policy_gate.sh)
    │
    ├─→ ALLOW_AUTONOMY=true? YES → Continue
    └─→ ALLOW_AUTONOMY=true? NO  → Exit (1)
              │
              ▼
Route Task + Execute
    │
    ├─→ SolOSRouter (classify)
    ├─→ SolOSImplementer (execute changes)
    ├─→ SolOSReviewer (validate post-change)
    └─→ SolManager (aggregate + log)
              │
              ▼
    Execution Summary
    (runtime/reports/)
              │
              ▼
    OS_EVOLUTION_LOG.md
    (append entry)
```

**Safety Features:**
- ✅ Atomic operations (all-or-nothing)
- ✅ Reversible (previous state backed up)
- ✅ Logged (all changes recorded)
- ✅ Policy-gated (ALLOW_AUTONOMY required)

---

## 🔐 Governance Model

### Execution Gate

**File:** `scripts/check_policy_gate.sh`

**Logic:**
```bash
if [[ "$1" == "execute" ]] && [[ "$ALLOW_AUTONOMY" != "true" ]]; then
    echo "ERROR: Execute mode requires ALLOW_AUTONOMY=true"
    exit 1  # Hard deny
fi
```

**Effect:**
- Proposal mode: Always allowed
- Execute mode: Blocked unless explicitly gated

**Usage:**
```bash
# Blocked
python3 scripts/route_task.py --task "..." --execute
# ERROR: policy gate denied

# Allowed
ALLOW_AUTONOMY=true python3 scripts/route_task.py --task "..." --execute
# OK: Executing...
```

### Governance Rules

**File:** `.vscode/sol-os/policies/governance.policy.md`

**Key Rules:**
1. All changes must be atomic
2. All changes must be reversible (with backups)
3. All changes must be logged to OS_EVOLUTION_LOG.md
4. Execute mode requires human-gated approval (ALLOW_AUTONOMY)
5. Proposal mode always available for visibility

---

## 📊 Data Flow

### Configuration Files

**config/fleet.json** — Provider roster
```json
{
  "providers": {
    "copilot-cli": {
      "backend": "foundry-local",
      "model": "qwen3.5-2b",
      "endpoint": "http://127.0.0.1:5272",
      "timeout_seconds": 30
    },
    "foundry-local": {
      "endpoint": "http://127.0.0.1:5272",
      "model": "qwen3.5-2b"
    }
  },
  "agents": [
    { "id": "solmanager", "provider": "copilot-cli", "role": "orchestration" },
    { "id": "solosrouter", "provider": "copilot-cli", "role": "routing" },
    { "id": "solosimplementer", "provider": "copilot-cli", "role": "implementation" },
    { "id": "solosreviewer", "provider": "copilot-cli", "role": "review" },
    { "id": "solossysops", "provider": "foundry-local", "role": "diagnostics" }
  ]
}
```

**config/mcp.servers.json** — MCP tool declarations
```json
{
  "filesystem": {
    "transport": "stdio",
    "command": "npx",
    "args": ["@modelcontextprotocol/server-filesystem", "./"]
  },
  "github": {
    "transport": "stdio",
    "command": "npx",
    "args": ["@modelcontextprotocol/server-github"]
  }
}
```

**config/router.rules.json** — Routing heuristics
```json
{
  "rules": [
    {
      "intent_pattern": "implement|code|generate",
      "agent": "solosimplementer",
      "confidence_threshold": 0.8
    },
    {
      "intent_pattern": "validate|review|check",
      "agent": "solosreviewer",
      "confidence_threshold": 0.7
    }
  ]
}
```

---

## 🗂️ Runtime Artifacts

### runtime/plans/

Generated routing and execution plans:
- `task_routing_TIMESTAMP.json` — Routing plan
- `task_execution_TIMESTAMP.json` — Execution plan

### runtime/reports/

Execution reports and proposals:
- `proposal_latest.md` — Latest proposal
- `execution_summary_TIMESTAMP.json` — Execution results
- `governance_report_TIMESTAMP.md` — Policy enforcement report

### runtime/logs/

System and provider logs:
- `foundry-local.meta.json` — Foundry Local metadata
- `copilot_cli.log` — Copilot CLI debug logs
- `provider_probe.log` — Provider health check logs

### OS_EVOLUTION_LOG.md

Master log of all applied changes:
```markdown
## v3.2.5 (2026-05-09)

### Summary
- Updated copilot-cli provider to route through Foundry Local
- Enhanced token sanitization for modern PAT format

### Reason
Eliminate GitHub Copilot CLI dependency, improve determinism

### Changes
- Modified: scripts/copilot_cli_adapter.py
- Modified: scripts/copilot_cli_doctor.py
- Added: config/fleet.json backend routing

### Rollback
git revert <sha>
```

---

## 🔌 Integration Points

### GitHub Automation

**File:** `.github/workflows/autonomous-proposals.yml`

**Triggers:**
- Schedule: Every 6 hours
- Manual dispatch (workflow_dispatch)

**Actions:**
1. Checkout repo
2. Run `python3 scripts/autonomous_cycle.py --task "governance audit" --ticks 1`
3. Generate proposal artifact
4. (Optional) Create pull request

### VS Code Integration

**File:** `.vscode/tasks.json`

**19 Task Definitions:**
- Routing tasks (route, route+execute, autonomy cycle)
- Diagnostic tasks (provider probe, MCP probe, auth check)
- Foundry tasks (bootstrap, status, restart, logs)
- Governance tasks (self-heal, self-evolve, proposal pack)

### IDE Agents

**File:** `.github/agents/*.agent.md`

**Integration:**
- VS Code agent chat (@solmanager, @solosrouter, etc.)
- GitHub Copilot extensions
- Custom agent mode registration

---

## 🧬 Autonomous Cycle

**File:** `scripts/autonomous_cycle.py`

**Algorithm:**

```
for tick in range(ticks):
    # Phase 1: Plan
    plan = route_task(task)
    
    # Phase 2: Propose
    proposal = generate_proposal(plan)
    
    # Phase 3: Review
    review = validate_proposal(proposal)
    
    # Phase 4: Execute (if approved)
    if review.approved and ALLOW_AUTONOMY:
        result = execute_proposal(proposal)
        log_to_evolution_log(result)
    else:
        print("Proposal requires human review")
        break

    # Generate report
    write_report(plan, proposal, review, result)
```

**Output:**
- Multi-tick reports in `runtime/reports/`
- Cumulative evolution log entries
- Failure handling (non-fatal, continue to next tick)

---

## 📈 Performance Characteristics

### Latency Profile

| Operation | Latency | Notes |
|---|---|---|
| Intent classification (Router) | 800-1200ms | Qwen 3.5 2B, local |
| Code generation (Implementer) | 1200-2000ms | Longer context |
| Validation (Reviewer) | 400-800ms | Quick checks |
| Health checks (SysOps) | 100-300ms | Direct HTTP probes |
| Full cycle (all agents) | 3000-5000ms | Serial execution |

### Resource Usage

| Component | CPU | Memory | Disk |
|---|---|---|---|
| Qwen 3.5 2B model | 2-4 vCPU | 6-8 GB | 2.5 GB (quantized) |
| Python runtime | 0.5-1 vCPU | 200-400 MB | 50 MB |
| MCP servers | 0.2-0.5 vCPU | 50-100 MB | 100 MB |
| **Total** | **3-6 vCPU** | **7-9 GB** | **2.7 GB** |

---

## 🔍 Debugging & Diagnostics

### Provider Status

```bash
python3 scripts/provider_probe.py
```

Output:
```
copilotCli ..................... ✓ ready (backend=foundry-local)
foundryLocal ................... ✓ ready (model=qwen3.5-2b)
mcp ............................ ✓ ready (3 servers)
```

### MCP Server Diagnostics

```bash
python3 scripts/mcp_probe.py
```

Output:
```
filesystem ..................... ✓ online (stdio)
github ......................... ✓ online (stdio)
foundry-local .................. ✓ online (HTTP)
```

### Copilot CLI Status

```bash
python3 scripts/copilot_cli_doctor.py --format plain
```

Output:
```
COPILOT_STATUS=ready
backend=foundry-local
model=qwen3.5-2b
timeout_seconds=30
```

---

## 🎓 Extending SolVS

### Add a Custom Agent

1. Create `.github/agents/my-agent.agent.md`
2. Define system prompt and instructions
3. Register in `config/fleet.json`
4. Route to agent from SolOSRouter

### Add a Custom MCP Server

1. Install MCP server package (e.g., `npm install @modelcontextprotocol/server-custom`)
2. Add to `config/mcp.servers.json`
3. Test with `python3 scripts/mcp_probe.py`
4. Use tool in agent prompts

### Add a Custom Provider

1. Implement adapter in `scripts/`
2. Register in `config/fleet.json`
3. Add provider routing logic to `route_task.py`
4. Test with `provider_probe.py`

---

## 📚 References

- **Foundry Local:** https://docs.foundryaas.com/
- **MCP Protocol:** https://modelcontextprotocol.io/
- **Copilot CLI:** https://github.blog/changelog/2024-04-29-github-copilot-command-line-interface/
- **Qwen Models:** https://huggingface.co/collections/Qwen/qwen-models-65c0a2f577b1ecb76d786745

---

**Last Updated:** 2026-05-10  
**Status:** Production-Ready (v3.2+)
