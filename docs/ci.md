# CI

This repo is **public**. Anyone can fork it and open a PR. The CI workflow must assume a hostile PR body and protect every secret accordingly.

## Trust boundary

| Surface | Visibility | Holds secrets? |
|---|---|---|
| Repo source, Issues, PRs, Actions logs | Public | no |
| HCP Terraform workspace | Private (HCP) | yes — all Terraform-time secrets |
| GitHub Actions encrypted secrets | Private (org/repo settings) | yes — only `TF_API_TOKEN` |
| `terraform plan` output | Public (posted to PR by HCP VCS integration) | redacted by HCP |

## Workflows

### `plan` — runs on PRs

- **Trigger**: `pull_request` against `main`.
- **PRs from branches in this repo** (collaborators): plan runs automatically.
- **PRs from forks**: plan runs only when a maintainer applies the `safe-to-plan` label. Until labeled, CI runs lint/validate only (no secrets, no HCP API token).
- **What it does**: calls the HCP Terraform API to start a speculative plan in the relevant workspace. HCP posts the plan summary back to the PR.
- **What it does NOT do**: never runs `terraform apply`, never echoes secret values, never reads `${{ secrets.* }}` into shell variables.

### `apply` — runs on main

- **Trigger**: `push` to `main` (i.e. merged PR).
- HCP creates a run for each VCS-watched workspace.
- **Manual confirmation required** in HCP UI by a workspace admin. No auto-apply for the prod workspaces.
- Apply logs are visible in HCP, not in GitHub Actions.

### `lint` — runs on every PR including forks

- `terraform fmt -check`, `terraform validate`, `tflint` if adopted.
- No secrets, no network calls beyond provider schema downloads.
- Safe to run unconditionally on fork PRs.

## Rules

1. **Never use `pull_request_target`** unless the workflow is reviewed line-by-line for fork-PR safety. The default trigger is `pull_request`, which gives fork PRs no access to secrets.
2. **Never `echo` secrets**, never pass them as command-line args (visible in `ps`). Use env vars and let the tool read them.
3. **Sensitive Terraform outputs**: mark `sensitive = true` on any output that could leak a value. HCP redacts these from plan output.
4. **Fork-PR plans are opt-in.** A maintainer reviews the diff, decides whether it's safe to run against the real Cloudflare/GitHub account, then applies the label.
5. **Apply requires a human.** No automated apply to a production workspace, ever.

## What to watch for in PR diffs from forks

Before applying `safe-to-plan`, scan the diff for:

- New `local_file` / `null_resource` / `external` data sources — these can exfiltrate values during a plan.
- New providers or modules pulled from untrusted sources — they execute code during `terraform init`.
- Changes to the workflow files themselves — fork-PR workflows run from the PR branch, so a malicious workflow edit is just as dangerous as malicious Terraform.
- Anything that reads a sensitive variable and writes it somewhere observable (a resource attribute, an output, a log).

If anything looks off, decline the label and ask for changes.
