# docs/

Operational documentation for the `perishdev/infra` repo. The [top-level `CLAUDE.md`](../CLAUDE.md) holds the locked design decisions; the docs below explain how those decisions play out in day-to-day use.

## Reading order for first contact

1. [`../CLAUDE.md`](../CLAUDE.md) — design decisions table. Authoritative.
2. [`../README.md`](../README.md) — what this repo is.
3. [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — five-minute orientation for contributors and AI agents.
4. [`state.md`](./state.md) — how HCP state is structured + the API access pattern.
5. [`ci.md`](./ci.md) — the required-checks contract for any merge.

The rest is reference, dipped into as needed.

## Reference

### Setup and onboarding

- [`setup.md`](./setup.md) — one-time bootstrap of HCP, Cloudflare token, GitHub App, local dev. Done once per maintainer's laptop.
- [`import.md`](./import.md) — `cf-terraforming` runbook for adopting existing Cloudflare state into Terraform.
- [`worktree-workflow.md`](./worktree-workflow.md) — optional `git worktree` convention for maintainers juggling multiple branches.

### Design contracts

- [`secrets.md`](./secrets.md) — where every secret lives, how rotation works, what isn't a secret.
- [`state.md`](./state.md) — HCP backend, workspace layout, API access from CLI.
- [`ci.md`](./ci.md) — workflow contract, fork-PR policy, branch protection requirements.

### Operations

- [`recipes.md`](./recipes.md) — common-task recipes: add a DNS record, add a repo, add a label, bump a provider, cross-workspace changes.
- [`rollback.md`](./rollback.md) — six options when an apply made things worse, ranked from cheapest to last-resort.
- [`hcp-api.md`](./hcp-api.md) — HCP REST API toolkit. Read plan summaries, confirm applies, find runs, all from `curl`.
- [`limits.md`](./limits.md) — vendor free-tier limits and where the cliffs are.

## When to add a new doc

Add a new file when:

- A future maintainer or agent will need to look something up by topic. The lookup should be a single grep / open.
- The information isn't easily derived from reading code or running a command.
- The information will be stable for at least a few months — short-lived state goes in commit messages, PR descriptions, or issue threads.

Don't add a new file for:

- One-off tasks (PR description suffices).
- Things that duplicate provider documentation (link to the vendor instead).
- Things that contradict [`../CLAUDE.md`](../CLAUDE.md) — fix the design decisions table first, then write the doc.

## When to delete a doc

When it's wrong and not worth fixing. A wrong doc is worse than no doc.
