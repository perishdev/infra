# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

This repository is bootstrapping. Only `LICENSE` exists so far. Treat any "common commands" or "architecture" sections as **not yet established** — discover, don't invent. When asked to add infrastructure, propose the layout in conversation (or a doc PR) before writing code, per the user's Document-Driven Development workflow.

## Intent

`perishdev/infra` manages the infrastructure for Perish's own apps and services (not a package index). It is modeled on [`pypi/infra`](https://github.com/pypi/infra):

- **SaltStack** for configuration management — expect `salt/` (states, formulas) and `pillar/` (per-host/per-env data, with secrets encrypted at rest).
- **Terraform** for cloud provisioning — expect `terraform/` organized per provider/environment, with remote state.
- A top-level `Makefile` is the canonical entrypoint for lint/test/apply targets in pypi/infra; mirror that pattern here when the first targets land.

When deciding where something goes, check how `pypi/infra` does it first and follow that convention unless there's a reason to diverge — then document the divergence.

## Conventions specific to this repo

- **Secrets**: never commit plaintext secrets, and never commit encrypted secrets either — sensitive data lives outside the repo entirely. See [`docs/secrets.md`](./docs/secrets.md).
- **Environments**: keep `production` / `staging` / etc. clearly separated in both Salt pillars and Terraform workspaces/dirs. A change to one environment must never silently apply to another.
- **Plan before apply**: for any Terraform change, run `terraform plan` and review output before `apply`. Do not auto-apply production workspaces.

## Locked design decisions

These are the contracts the repo is built on. Don't re-derive; if changing, update the linked docs first.

| Concern | Decision | Doc |
|---|---|---|
| Terraform-time secrets store | HCP Terraform workspace variables (sensitive) | [`docs/secrets.md`](./docs/secrets.md) |
| CI-time secrets store | GitHub Actions encrypted secrets (only `TF_API_TOKEN`) | [`docs/secrets.md`](./docs/secrets.md) |
| Terraform state backend | HCP Terraform (managed) | [`docs/state.md`](./docs/state.md) |
| GitHub auth from Terraform | GitHub App (not PAT) | [`docs/secrets.md`](./docs/secrets.md) |
| CI plan/apply policy | Plan-on-PR (collaborator auto, fork PRs require `safe-to-plan` label); apply gated to `main` + manual confirmation in HCP | [`docs/ci.md`](./docs/ci.md) |
| At-rest encryption in repo | None — nothing encrypted committed; sensitive pillar data fetched at deploy time | [`docs/secrets.md`](./docs/secrets.md) |

## Inherited from the user's global CLAUDE.md (highlights)

- Conventional Commits for commit messages, Conventional Branch for branch names, Conventional PR action format for PR titles.
- Python is the default for any tooling/scripts; use `uv`; type hints; PEP 8.
- Ask clarifying questions before large changes.
- Never add `claude.ai/code` as a co-author or collaborator.
