# Setup

One-time, out-of-band steps to wire up the systems this repo manages. The repo's Terraform code is speculative until these are done.

Run in order. Each step explains what it produces and where the value goes.

## 1. HCP Terraform — organization

1. Sign up at <https://app.terraform.io/> (free tier is sufficient to start).
2. Create an organization named **`perishdev`** (must match the `organization` field in every `terraform/*/versions.tf`).
3. Inside the org, create a project named **`infra`**.

## 2. HCP Terraform — workspaces

For each Terraform leaf directory, create a VCS-linked workspace under the `infra` project:

| Leaf | Workspace name | VCS working directory |
|---|---|---|
| `terraform/cloudflare/` | `cloudflare` | `terraform/cloudflare` |
| `terraform/github/` | `github-org` | `terraform/github` |

For each workspace:

- VCS provider: GitHub (connect via OAuth, scope to this repo only).
- Trigger runs only on changes to the working directory above.
- Execution mode: **Remote**.
- Auto-apply: **disabled** (manual confirmation required).
- For fork PRs, **disable speculative plans** in workspace settings — otherwise HCP runs plans with workspace variables exposed to anyone who can open a PR. The label-gated plan flow in [`ci.md`](./ci.md) replaces this.

## 3. Cloudflare API token

1. Cloudflare dashboard → My Profile → API Tokens → Create Token.
2. Use the **"Custom token"** template with these permissions for the `perish.dev` zone and the account it belongs to:
   - Zone — DNS — Edit
   - Zone — Zone Settings — Edit
   - Zone — Workers Routes — Edit
   - Account — Workers Scripts — Edit
   - Account — Workers R2 Storage — Edit
   - Account — Cloudflare Pages — Edit
3. Account Resources: **Include — your account only**. Zone Resources: **Include — Specific zone — `perish.dev`**.
4. Copy the token (shown once).
5. In HCP Terraform → workspace **`cloudflare`** → Variables → add `cloudflare_api_token` as a **Terraform variable**, mark **Sensitive**, paste the token.

## 4. GitHub App

The `github-org` workspace authenticates as a GitHub App, not a PAT.

1. Org settings → Developer settings → GitHub Apps → New GitHub App.
2. Permissions (start narrow, widen on demand):
   - Repository permissions: Administration (read/write), Contents (read), Metadata (read), Pull requests (read/write).
   - Organization permissions: Members (read), Administration (read/write).
3. Where can this app be installed: **Only on this account**.
4. Create. Note the **App ID**.
5. Generate a **private key** (downloads as a `.pem`). Treat it like a password.
6. Install the app on the `perishdev` org, scoped to "All repositories" (or to specific ones; can be widened later). Note the **Installation ID** from the install URL.
7. In HCP Terraform → workspace **`github-org`** → Variables → add three sensitive Terraform variables:
   - `github_owner` = `perishdev` (not sensitive)
   - `github_app_id` = the App ID (sensitive)
   - `github_app_installation_id` = the Installation ID (sensitive)
   - `github_app_pem` = paste the PEM contents (sensitive)

## 5. HCP Terraform API token for CI

Only needed if/when CI workflows trigger HCP runs (the current [`ci.yml`](../.github/workflows/ci.yml) doesn't — it only runs fmt/validate locally on the runner). Skip until needed.

When needed:

1. HCP Terraform → User settings → Tokens → Create API token. Scope: minimal.
2. GitHub → repo settings → Secrets → New repository secret → `TF_API_TOKEN`.

## 6. Local development

For running `make validate` / `make plan` from your laptop:

1. Install Terraform ≥ 1.9.
2. `terraform login` — opens a browser, asks HCP for an API token tied to your user. Token lands in `~/.terraform.d/credentials.tfrc.json`.
3. From any leaf dir: `terraform init` (will authenticate to HCP automatically).

## 7. Importing existing Cloudflare resources

See [`import.md`](./import.md) for the `cf-terraforming` runbook. It uses Cloudflare's own CLI to generate HCL + `import` blocks for the existing zone, R2 buckets, and Pages projects.
