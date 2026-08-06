# docs/

Operational documentation for the `perishdev/infra` repo. The [top-level `CLAUDE.md`](../CLAUDE.md) holds the locked design decisions; the docs below explain how those decisions play out in day-to-day use.

Generic setup/import/CI/HCP-API/secrets/state **procedure** lives in the [infra-copilot plugin](https://github.com/hasansezertasan/infra-copilot). This directory holds perish.dev-specific operations and decisions.

## Reading order for first contact

1. [`../CLAUDE.md`](../CLAUDE.md) — design decisions table. Authoritative.
2. [`../README.md`](../README.md) — what this repo is.
3. [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — five-minute orientation for contributors and AI agents.
4. [`decisions.md`](./decisions.md) — perish.dev-specific decisions and live resource facts.

The rest is reference, dipped into as needed.

## Reference

- [`decisions.md`](./decisions.md) — perish.dev-specific decisions (Cloudflare import scope) and live resource IDs (HCP org/workspace IDs, status-check ID).
- [`limits.md`](./limits.md) — vendor free-tier limits and where the cliffs are.
- [`recipes.md`](./recipes.md) — common-task recipes: add a DNS record, add a repo, add a label, bump a provider, cross-workspace changes.
- [`rollback.md`](./rollback.md) — six options when an apply made things worse, ranked from cheapest to last-resort.

## When to add a new doc

Add a new file when:

- A future maintainer or agent will need to look something up by topic. The lookup should be a single grep / open.
- The information isn't easily derived from reading code or running a command.
- The information will be stable for at least a few months — short-lived state goes in commit messages, PR descriptions, or issue threads.

Don't add a new file for:

- One-off tasks (PR description suffices).
- Things that duplicate provider documentation (link to the vendor instead).
- Generic procedure that applies to any infra-copilot-managed repo — that belongs in the [infra-copilot plugin](https://github.com/hasansezertasan/infra-copilot), not here.
- Things that contradict [`../CLAUDE.md`](../CLAUDE.md) — fix the design decisions table first, then write the doc.

## When to delete a doc

When it's wrong and not worth fixing. A wrong doc is worse than no doc.
