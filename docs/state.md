# Terraform state

State lives in **HCP Terraform** (formerly Terraform Cloud). It is never stored locally, never committed, and never exposed to public CI logs.

## Why HCP Terraform

- Managed remote backend with built-in locking — no S3 + DynamoDB to operate.
- Runs execute on HCP infrastructure, so the Cloudflare token / GitHub App key never leave HCP and never appear in GitHub Actions logs.
- Free tier covers small teams. Easy to migrate off later (state is just a JSON blob).

## Organization

- **HCP org**: `perishdev` (one org per company).
- **Project**: `infra` (one project per repo).

## Workspaces

One workspace per concern. Start with the minimum and split per environment only when a change to one environment must not affect another (different account, different apex domain, or a real isolation requirement).

| Workspace | Purpose | Auto-apply? |
|---|---|---|
| `cloudflare` | Cloudflare zone, DNS, Workers, R2 for the one apex domain we manage | no — manual apply |
| `github-org` | GitHub org, repos, teams, branch protection | no — manual apply |

Today there is no separate `cloudflare-staging` workspace because we manage a single apex domain in a single Cloudflare account. Staging surfaces (`staging.<domain>`, `app-staging` Worker, etc.) live as additional resources inside the `cloudflare` workspace. Revisit if we add a second apex domain dedicated to staging or move staging into a separate Cloudflare account.

Workspaces are wired to the `main` branch of this repo via VCS integration. Plans run on PRs (see [`ci.md`](./ci.md)); applies require manual confirmation in HCP.

## Variables

Each workspace declares:

- **Terraform variables** (non-sensitive): account IDs, zone IDs, region names, repo names.
- **Sensitive variables**: Cloudflare API token, GitHub App credentials (App ID, installation ID, PEM). Marked `sensitive` so HCP redacts them from logs.
- **Environment variables**: rarely needed; only for provider-level config that must be in env (e.g. `TF_LOG`).

Variable values live in HCP, not in the repo. The repo declares `variable "x" {}` blocks; HCP supplies the values.

## Access

- **Read state**: workspace members in HCP (small, named list).
- **Trigger runs**: anyone who can open a PR triggers a plan; only workspace admins can confirm an apply.
- **Manage workspace settings**: org admins only.

## Migrating away

If HCP ever stops being the right choice: `terraform state pull` from each workspace → `terraform state push` into the new backend. Code stays unchanged except for the `backend` block. This is the main reason for picking a managed backend now rather than self-hosting state on day one.
