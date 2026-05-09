# GitHub Automation

## Scheduled execution

The fleet includes a scheduled workflow at `.github/workflows/autonomous-proposals.yml`.

It does the following:

- validates the repository scaffold
- probes configured MCP servers
- runs the autonomous cycle in proposal mode
- uploads runtime artifacts
- opens or updates a pull request containing proposal artifacts

## Expected outputs

The workflow refreshes files under `runtime/reports/` and `runtime/plans/`.

The pull request body is sourced from `runtime/reports/proposal_latest.md`.

## Notes

- MCP probe failures are non-blocking by default so the fleet can still generate a proposal.
- The created pull request is artifact-oriented: it carries plan and report files for human review.
- Apply actions remain human-gated in the scripts themselves.
