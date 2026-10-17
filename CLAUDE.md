# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

Active. The repo manages live infrastructure for `perish.dev` via Terraform against HCP. Discover existing layout in `terraform/` and `docs/` before proposing changes; for anything new, propose the layout in conversation (or a doc PR) before writing code, per the user's Document-Driven Development workflow.

## Intent

`perishdev/infra` manages the infrastructure for Perish's own apps and services. Everything currently in scope is SaaS-shaped — Cloudflare for DNS / Email Routing / R2 / Workers, GitHub for repos and Pages, HCP for Terraform state and runs. There are no hosts we operate ourselves.

- **Terraform** for cloud provisioning — `terraform/<provider>/` per leaf, one leaf per HCP workspace, remote state in HCP Terraform.
- **GitHub Actions** for fork-safe `fmt` / `validate` gates, and plan / apply for leaves that have moved off HCP (state in R2); HCP for plan / apply on the rest, via VCS integration.

The repo is inspired by [`pypi/infra`](https://github.com/pypi/infra) but does not follow it 1:1 — pypi.org runs a host fleet (Warehouse, mirrors, build hosts) that requires configuration management; we don't. If we ever do, the choice between SaltStack, Ansible, image-baking (Packer), NixOS, or Kubernetes-native config will be made then. Until that day, *no config management tool ships in this repo*.

## Conventions specific to this repo

- **Secrets**: never commit plaintext secrets, and never commit encrypted secrets either — sensitive data lives outside the repo entirely. See the [infra-copilot plugin](https://github.com/hasansezertasan/infra-copilot)'s secrets reference.
- **Environments**: single Cloudflare account, single apex domain today. If/when a staging surface is added, keep it separated at the Terraform workspace level (not just the resource level) so a change to one environment can't silently apply to another.
- **Plan before apply**: every Terraform change goes through `terraform plan` (locally or as an HCP speculative run on a PR) and is reviewed before `apply`. `terraform/github` auto-applies on merge, with the PR's plan as the approval (**Terraform CI apply** in [`.infra-copilot/decisions.md`](./.infra-copilot/decisions.md)); `terraform/cloudflare` is still confirmed by hand in HCP until its cutover.

## Locked design decisions

The contracts the repo is built on live in [`.infra-copilot/decisions.md`](./.infra-copilot/decisions.md), one row per decision with a status (`proposed`, `locked`, `superseded`). Don't re-derive them; to change one, update that file first, in the same PR as the code it governs. Public identifiers (org, zone, account IDs) live in [`.infra-copilot/config.md`](./.infra-copilot/config.md).

The move from HCP to R2 state and GitHub Actions is recorded there as **Terraform CI migration** and is `locked`, in progress: `terraform/github` has cut over; until `terraform/cloudflare` does, the HCP rows in that file still hold for it.

## Inherited from the user's global CLAUDE.md (highlights)

- Conventional Commits for commit messages, Conventional Branch for branch names, Conventional PR action format for PR titles.
- Python is the default for any tooling/scripts; use `uv`; type hints; PEP 8.
- Ask clarifying questions before large changes.
- Never add `claude.ai/code` as a co-author or collaborator.
