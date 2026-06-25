# Contributing

A 5-minute orientation for anyone — human or AI agent — picking up work on this repo for the first time.

## The mental model

This repo manages SaaS-shaped infrastructure for [`perish.dev`](https://perish.dev) — Cloudflare (DNS, Email Routing, etc.) and GitHub (org repos, branch protection, labels), all through Terraform with HCP Terraform as the state backend.

There are no servers, no containers, no Kubernetes manifests. Every resource maps to a managed service.

## Read these first, in this order

1. **[`CLAUDE.md`](./CLAUDE.md)** — design decisions table. Authoritative. Don't re-derive any decision listed there; if you want to change one, update the doc first.
2. **[`README.md`](./README.md)** — what's where.
3. **[`docs/state.md`](./docs/state.md)** — how Terraform state is structured and how to read HCP via API.
4. **[`docs/ci.md`](./docs/ci.md)** — the required checks for any PR to land.
5. **[`docs/setup.md`](./docs/setup.md)** — bootstrap (skip this if HCP + GitHub App are already wired; you'd know).

## The PR workflow

Every change is a PR. Even one-line typos. Even your own. Branch protection on `main` enforces it.

### Branch naming

[Conventional Branch](https://conventional-branch.github.io/): `feat/<topic>`, `fix/<topic>`, `chore/<topic>`, `docs/<topic>`.

### Commit messages

[Conventional Commits](https://www.conventionalcommits.org/): `feat(scope): subject`, `fix(scope): subject`, `docs: subject`, etc. Scope is usually the affected directory (`cloudflare`, `github`, `hcp`).

### PR title

[Conventional PR action format](https://github.com/marketplace/actions/conventional-pull-request) — same prefix rules as commits. Squash-merge collapses the branch's commits into the PR title, so the PR title becomes the commit subject on `main`.

### Required checks

Four checks must pass before merge:

- `terraform fmt`
- `terraform validate (terraform/cloudflare)`
- `terraform validate (terraform/github)`
- `Terraform Cloud/perishdev/…` — HCP's aggregated commit status

The first three run on every PR (including from forks). The HCP check fires per-workspace when a workspace's path filter matches the diff; otherwise HCP rolls up to a single SUCCESS. Docs-only PRs pass cleanly.

### Fork PRs

A maintainer applies the `safe-to-plan` label to authorise HCP speculative plans on a fork PR. Without it, only the fork-safe GH Actions checks run. See [`docs/ci.md`](./docs/ci.md) for the threat model and what to scan for before labelling.

## Where things go

Match the change to the right leaf:

| Want to change | File |
|---|---|
| DNS records on `perish.dev` | [`terraform/cloudflare/dns.tf`](./terraform/cloudflare/dns.tf) |
| Cloudflare zone settings | [`terraform/cloudflare/main.tf`](./terraform/cloudflare/main.tf) |
| Repo settings or new repo | [`terraform/github/repos.tf`](./terraform/github/repos.tf) |
| Branch protection rules | [`terraform/github/branch_protection.tf`](./terraform/github/branch_protection.tf) |
| Issue / PR labels | [`terraform/github/labels.tf`](./terraform/github/labels.tf) |
| New HCP workspace, project, VCS link | not yet code; see [Issue #8](https://github.com/perishdev/infra/issues/8) |
| Anything new (GCP, AWS, etc.) | new leaf `terraform/<concern>/` — see [`terraform/README.md`](./terraform/README.md) |

## Local development

```sh
brew install terraform                       # ≥ 1.9
brew install gh                              # for PRs
terraform login                              # writes ~/.terraform.d/credentials.tfrc.json

cd terraform/cloudflare                      # or terraform/github
terraform init
terraform plan                               # speculative; runs in HCP, output streams back
```

`terraform apply` from CLI is blocked on VCS-connected workspaces. Apply happens via HCP when a PR merges to `main`.

## API tricks worth knowing

### Read HCP plan summary without opening the UI

`terraform login` stores a usable HCP API token. From there:

```sh
HCP_TOKEN=$(jq -r '.credentials["app.terraform.io"].token' ~/.terraform.d/credentials.tfrc.json)

# Find your PR's run
curl -s "https://app.terraform.io/api/v2/workspaces/<workspace-id>/runs?filter%5Bstatus%5D=planned_and_finished" \
  -H "Authorization: Bearer $HCP_TOKEN" | jq '.data[0]'

# Read structured plan diff
PLAN_ID=...
curl -sL "https://app.terraform.io/api/v2/plans/$PLAN_ID/json-output-redacted" \
  -H "Authorization: Bearer $HCP_TOKEN" \
  | jq '.resource_changes[] | {address, actions: .change.actions}'
```

Workspace IDs are in [`docs/state.md`](./docs/state.md).

### Confirm apply via API

```sh
curl -s -X POST "https://app.terraform.io/api/v2/runs/<run-id>/actions/apply" \
  -H "Authorization: Bearer $HCP_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{"comment":"reviewed plan via API"}'
```

This counts as the manual confirm — same gate, scripted.

## Things to know that aren't in the design decisions

- **The HCP required-status-check name (`Terraform Cloud/perishdev/repo-id-CffUfWW6H1x6Bauq`) embeds a per-installation VCS ID.** If the GitHub-HCP OAuth connection is ever rebuilt, that string changes and every PR is silently blocked until [`terraform/github/branch_protection.tf`](./terraform/github/branch_protection.tf) is updated. Lives in three places (this file, [`docs/ci.md`](./docs/ci.md), inline in the resource) so future-you finds it from any angle.
- **GitHub Pages cert provisioning can wedge.** Fix: `gh api -X PUT repos/<owner>/<repo>/pages -f 'cname='` then re-set the CNAME. See troubleshooting in [`docs/setup.md`](./docs/setup.md).
- **cf-terraforming is for one-time onboarding**, not steady-state. New Cloudflare resources should be written in Terraform directly, not discovered after the fact. See [`docs/import.md`](./docs/import.md).
- **`tfe_workspace.*` doesn't exist yet.** HCP itself isn't Terraform-managed today; settings clicked into the UI. See [Issue #8](https://github.com/perishdev/infra/issues/8) for the planned arc.

## What not to do

- Don't put secrets in code, in `.tfvars` files, in commit messages, or in CI logs. Sensitive workspace variables live only in HCP.
- Don't bypass branch protection by force-pushing to `main`. It's blocked at the GitHub level, but if you're an admin and tempted: don't.
- Don't add `claude.ai/code` as a Co-Authored-By trailer or collaborator. Policy.
- Don't add features that don't have a use case today. YAGNI applies — the repo deliberately has no Salt, no Ansible, no module abstraction yet.

## When you're done

- Open the PR. Wait for the 4 checks. Read the HCP plan summary (UI or API). Merge.
- If the change was a Terraform apply, confirm in HCP (or via API). Watch for `applied` status.
- Update [`docs/`](./docs/) if any of the design decisions or operational details shifted.

## Questions

If something here doesn't match what you observe, the docs are wrong — open a `docs:` PR. The repo is small enough that "doc drift" is a real risk and worth fixing on sight.
