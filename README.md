# infra

There is dust in the clouds, infrastructure as code for perishdev.

## What this repo manages

- **Cloudflare** — the `perish.dev` zone, all DNS records (Email Routing + GitHub Pages), via the [`cloudflare/cloudflare`](https://registry.terraform.io/providers/cloudflare/cloudflare/latest) v5 Terraform provider.
- **GitHub** — `perishdev/infra` and `perishdev/perishdev.github.io` repo settings, branch protection on `main`, the `safe-to-plan` label, via the [`integrations/github`](https://registry.terraform.io/providers/integrations/github/latest) v6 Terraform provider.
- **HCP Terraform** — remote state, runs, and the workspace variables that hold the API credentials. The repo's own `terraform/cloud {}` block lives in each leaf's `versions.tf`.

No hosts of our own (no Salt, no Ansible). Everything in scope is SaaS-shaped.

## Setup — let an agent do it

Bootstrapping (or forking this repo as groundwork for another org) is **agent-first**.
Point any AI coding agent at the setup skill and it drives the whole thing — HCP,
Cloudflare token, GitHub App, importing existing resources, first plan — pausing only when
a human must sign up, mint a credential, or paste a secret.

- **Claude Code:** run `/infra-setup` (or just say "set up the infra").
- **Other harnesses (opencode, Codex, …):** open and follow the
  [infra-copilot plugin](https://github.com/hasansezertasan/infra-copilot)'s
  `skills/infra-setup/SKILL.md` — plain Markdown plus a machine-readable manifest; see
  [`AGENTS.md`](./AGENTS.md).

It's idempotent and resumable: re-invoke any time and it re-checks state, resuming at the
first incomplete step. For a human-driven bootstrap instead, the [infra-copilot plugin](https://github.com/hasansezertasan/infra-copilot)'s
setup reference is the canonical runbook the skill orchestrates.

## Where things live

```
terraform/
  cloudflare/   one HCP workspace (cloudflare),     zone + DNS
  github/       one HCP workspace (github-org),     repos + protection + labels
.claude/
  settings.json             enables the infra-copilot plugin (marketplace + plugin)
  infra-copilot.local.md    this repo's non-secret config the plugin reads at startup
.github/
  workflows/    fork-safe terraform fmt + validate gates
docs/
  decisions.md  perish.dev-specific decisions + live resource IDs
  recipes.md    common-task recipes
  rollback.md   what to do when an apply made things worse
  limits.md     vendor free-tier limits
AGENTS.md       cross-harness pointer for non-Claude agents
```

For the contracts the repo is built on — secrets, state, CI — see [`CLAUDE.md`](./CLAUDE.md). For the live design decisions table, look there first. The generic setup/import/CI/HCP-API/secrets/state procedure lives in the [infra-copilot plugin](https://github.com/hasansezertasan/infra-copilot).

## Contributing

Branch protection requires four green checks before any merge to `main`:

- `terraform fmt`
- `terraform validate (terraform/cloudflare)`
- `terraform validate (terraform/github)`
- `Terraform Cloud/perishdev/...` (the HCP aggregated commit status)

Fork PRs only get GitHub Actions; HCP plans require a maintainer to apply the `safe-to-plan` label first. See the [infra-copilot plugin](https://github.com/hasansezertasan/infra-copilot)'s CI reference for the full policy, and [`CLAUDE.md`](./CLAUDE.md) for the locked policy decision.

Conventional Commits, Conventional Branches, Conventional PR titles.

## License

[MIT](./LICENSE)
