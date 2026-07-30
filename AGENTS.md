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

- **Every change is a PR.** Branch protection on `main` requires four green checks; see
  [`docs/ci.md`](./docs/ci.md).
- **Never commit secrets** — not plaintext, not encrypted. Sensitive values live in HCP
  workspace variables. See [`docs/secrets.md`](./docs/secrets.md).
- **Plan before apply.** Applies are never automatic; a human (or an authenticated API
  call) confirms in HCP.
- Conventional Commits / Conventional Branches / Conventional PR titles.
- Operational reference lives in [`docs/`](./docs/): `state.md`, `secrets.md`, `ci.md`,
  `recipes.md`, `rollback.md`, `hcp-api.md`, `limits.md`.
