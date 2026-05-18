# CI Secrets for SolVS

This document explains recommended GitHub Actions secrets used by the repository and suggested scopes/policies.

Recommended secrets

- `COPILOT_PROVIDER_BASE_URL` — Base URL for your local Foundry or Copilot provider (e.g. `http://foundry.local:5272`).
  - Scope: repository Actions secrets. No wider access required.
  - Use: enables the optional `agents` job in `.github/workflows/ci.yml` so agent discovery tests run against a real provider.

- `COPILOT_BYOK_KEY` — Optional BYOK key or API key for provider authentication when the provider requires a key.
  - Scope: repository Actions secrets. Store as `secret string`.
  - Policy: rotate periodically and restrict to the minimal provider account with test-only permissions.

- `AUTONOMY_APPROVAL_TOKEN` — Only needed if CI will exercise provider `--execute` flows (not recommended for CI).
  - Scope: repository Actions secrets and never used in PRs from forks (do not expose to untrusted PRs).
  - Policy: require manual approval before enabling any CI job that uses this token.

Secrets storage recommendations

- Use GitHub Actions repository secrets (Settings → Secrets → Actions). For organization-level control, use organization secrets with repository access limited to this repo.
- Least privilege: create a dedicated service account for CI tests and restrict it to read-only or test-only actions on the provider.
- Short-lived keys: prefer rotating keys and use ephemeral credentials when possible.

Example secrets policy (recommended)

1. Create a CI service account scoped to test/probe actions only.
2. Issue a short-lived API key for that account.
3. Store the API key as `COPILOT_BYOK_KEY` in the repository's Actions secrets.
4. Only allow repository collaborators to add or update the secret.
5. Require pull request reviews and branch protection for `main` before merging changes that enable execute-mode CI.

Enabling `agents` job

The `agents` job in `.github/workflows/ci.yml` runs only when `COPILOT_PROVIDER_BASE_URL` is set in secrets. To enable it:

1. Add `COPILOT_PROVIDER_BASE_URL` and `COPILOT_BYOK_KEY` (if required) in repository Secrets.
2. Push a branch or open a PR to trigger the workflow.

Security note

Do not store long-lived operator tokens in CI for apply/execute flows. If required, gate execute-mode behind manual approvals and protect secrets from forked PR workflows.
