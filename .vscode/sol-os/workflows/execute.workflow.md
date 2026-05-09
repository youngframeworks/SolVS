# Workflow: execute

## Trigger
- Chat: `execute`
- CLI: `python3 scripts/route_task.py --task \"...\"`

## Sequence
1. Validate policy gate.
2. Classify intent with router rules.
3. Generate plan artifact.
4. Dispatch route through configured fleet.
5. Capture report.
