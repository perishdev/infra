# AGENTS.md

Guidance for any AI coding agent (Claude Code, opencode, Codex, Cursor, …) working in
this repo. Claude Code also reads [`CLAUDE.md`](./CLAUDE.md); the design decisions and
conventions there are authoritative for every agent — read it first.

## What this repo is

Infrastructure-as-code for `perish.dev`: Terraform against **HCP Terraform**, managing
**Cloudflare** (DNS, Email Routing) and **GitHub** (org repos, branch protection, labels).
No servers, no config management — everything is SaaS-shaped. See [`README.md`](./README.md).

## Bootstrapping the repo (or a fork for another org)

There is an **agent-first setup skill** at
[`.claude/skills/infra-setup/SKILL.md`](./.claude/skills/infra-setup/SKILL.md). It drives
the whole bootstrap — HCP, Cloudflare token, GitHub App, importing existing resources,
first plan — and pauses only for the steps a human must do (signups, minting credentials,
pasting secrets).

- **Claude Code:** run `/infra-setup`, or just ask to "set up the infra."
- **Other harnesses:** open and follow
  [`.claude/skills/infra-setup/SKILL.md`](./.claude/skills/infra-setup/SKILL.md) directly.
  It's plain Markdown plus a machine-readable manifest
  ([`references/steps.yaml`](./.claude/skills/infra-setup/references/steps.yaml)) — no
  Claude-Code-specific runtime is required to walk it.

The skill is **idempotent and resumable**: on every run it re-checks state and resumes at
the first incomplete step, so it's safe to re-invoke.

## Working conventions

Conventions and the locked design decisions are **authoritative in
[`CLAUDE.md`](./CLAUDE.md)** — read it; this file deliberately does not restate them (one
source of truth, no drift). The essentials it covers: every change is a PR (branch
protection on `main` needs four green checks), secrets never touch the repo (they live in
HCP workspace variables), applies are never automatic (a human or authenticated API call
confirms in HCP), and commits / branches / PR titles follow the Conventional * specs.

Operational reference lives in [`docs/`](./docs/): `decisions.md`, `recipes.md`,
`rollback.md`, `limits.md`. Generic setup/import/CI/HCP-API/secrets/state procedure
lives in the [infra-copilot plugin](https://github.com/hasansezertasan/infra-copilot).
