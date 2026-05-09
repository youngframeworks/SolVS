# Provider Badge Check

Task: badge refresh validation

## Summary
- Route rule: fallback
- Route: SolOSRouter -> SolOSImplementer -> SolOSReviewer
- Dispatch targets:
  - SolOSRouter via copilot-cli using MCP [filesystem, github, foundry-local]
  - SolOSImplementer via foundry-local using MCP [filesystem, github, foundry-local]
  - SolOSReviewer via copilot-cli using MCP [filesystem, github, foundry-local]

## Validation Artifacts
- Tick 1: route rc=0

## Proposed Pull Request Body
```markdown
## Automated proposal for: badge refresh validation

### What changed
- Generated route plan and dispatch metadata
- Ran autonomous governance cycle in proposal mode
- Produced machine-readable reports for review

### Review checklist
- [ ] Confirm selected route is correct
- [ ] Confirm MCP targets are reachable in your environment
- [ ] Approve or reject any follow-on apply action
```

<!-- provider-badges:start -->
## Provider Status Badges

![copilot-cli-plan-only](https://img.shields.io/badge/copilot-cli-plan-only-yellow)
![foundry-local-ready](https://img.shields.io/badge/foundry-local-ready-brightgreen)

Source: runtime/reports/route_summary_20260508T122447Z.json
<!-- provider-badges:end -->
