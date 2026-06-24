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

- **Secrets**: never commit plaintext secrets, even in pillar files. Decide on an encryption mechanism (SOPS, `git-crypt`, or salt's GPG renderer) before the first pillar is added, and document it here.
- **Environments**: keep `production` / `staging` / etc. clearly separated in both Salt pillars and Terraform workspaces/dirs. A change to one environment must never silently apply to another.
- **Plan before apply**: for any Terraform change, run `terraform plan` and review output before `apply`. Do not auto-apply.

## Inherited from the user's global CLAUDE.md (highlights)

- Conventional Commits for commit messages, Conventional Branch for branch names, Conventional PR action format for PR titles.
- Python is the default for any tooling/scripts; use `uv`; type hints; PEP 8.
- Ask clarifying questions before large changes.
- Never add `claude.ai/code` as a co-author or collaborator.
