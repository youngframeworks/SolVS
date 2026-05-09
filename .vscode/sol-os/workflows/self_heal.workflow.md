# Workflow: self_heal

## Purpose
Proposal-first drift detection and repair planning.

## Gate
Apply requires:
- `--apply`
- `--approval-token APPLY_SELF_HEAL`

## Command
- Proposal: `python3 scripts/self_heal.py`
- Apply: `python3 scripts/self_heal.py --apply --approval-token APPLY_SELF_HEAL`
