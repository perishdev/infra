# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

Active. The repo manages live infrastructure for `perish.dev` via Terraform against HCP. Discover existing layout in `terraform/` and `docs/` before proposing changes; for anything new, propose the layout in conversation (or a doc PR) before writing code, per the user's Document-Driven Development workflow.

## Intent

`perishdev/infra` manages the infrastructure for Perish's own apps and services. Everything currently in scope is SaaS-shaped — Cloudflare for DNS / Email Routing / R2 / Workers, GitHub for repos and Pages, HCP for Terraform state and runs. There are no hosts we operate ourselves.

- **Terraform** for cloud provisioning — `terraform/<provider>/` per leaf, one leaf per HCP workspace, remote state in HCP Terraform.
- **GitHub Actions** for fork-safe `fmt` / `validate` gates; HCP for plan / apply via VCS integration.

The repo is inspired by [`pypi/infra`](https://github.com/pypi/infra) but does not follow it 1:1 — pypi.org runs a host fleet (Warehouse, mirrors, build hosts) that requires configuration management; we don't. If we ever do, the choice between SaltStack, Ansible, image-baking (Packer), NixOS, or Kubernetes-native config will be made then. Until that day, *no config management tool ships in this repo*.

## Conventions specific to this repo

- **Secrets**: never commit plaintext secrets, and never commit encrypted secrets either — sensitive data lives outside the repo entirely. See [`docs/secrets.md`](./docs/secrets.md).
- **Environments**: single Cloudflare account, single apex domain today. If/when a staging surface is added, keep it separated at the Terraform workspace level (not just the resource level) so a change to one environment can't silently apply to another.
- **Plan before apply**: every Terraform change goes through `terraform plan` (locally or as an HCP speculative run on a PR) and is reviewed before `apply`. Production applies are never auto-applied.

## Locked design decisions

These are the contracts the repo is built on. Don't re-derive; if changing, update the linked docs first.

| Concern | Decision | Doc |
|---|---|---|
| Terraform-time secrets store | HCP Terraform workspace variables (sensitive) | [`docs/secrets.md`](./docs/secrets.md) |
| CI-time secrets store | GitHub Actions encrypted secrets (only `TF_API_TOKEN`) | [`docs/secrets.md`](./docs/secrets.md) |
| Terraform state backend | HCP Terraform (managed) | [`docs/state.md`](./docs/state.md) |
| GitHub auth from Terraform | GitHub App (not PAT) | [`docs/secrets.md`](./docs/secrets.md) |
| CI plan/apply policy | Plan-on-PR (collaborator auto, fork PRs require `safe-to-plan` label); apply gated to `main` + manual confirmation in HCP | [`docs/ci.md`](./docs/ci.md) |
| At-rest encryption in repo | None — nothing encrypted committed; anything sensitive lives in HCP workspace variables or external stores | [`docs/secrets.md`](./docs/secrets.md) |

## Inherited from the user's global CLAUDE.md (highlights)

- Conventional Commits for commit messages, Conventional Branch for branch names, Conventional PR action format for PR titles.
- Python is the default for any tooling/scripts; use `uv`; type hints; PEP 8.
- Ask clarifying questions before large changes.
- Never add `claude.ai/code` as a co-author or collaborator.
