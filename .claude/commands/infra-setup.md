---
description: Bootstrap this Terraform + HCP infra repo (or a fork for another org), agent-first with human-in-the-loop handoffs.
allowed-tools: Read, Bash, Edit, Write, Glob, Grep, AskUserQuestion, WebFetch
---

# /infra-setup

Explicit entry point for the [`infra-setup`](../skills/infra-setup/SKILL.md) skill.

Load `../skills/infra-setup/SKILL.md` and drive it end-to-end:

1. **Resume first.** Walk `../skills/infra-setup/references/steps.yaml` and run each step's
   `check` to find where setup already is. Report `✓` for green steps; resume at the first
   red one. Never assume state from a previous session.
2. **Respect the actor split.** Execute `AGENT` steps yourself. On a `HUMAN` step, stop and
   emit the handoff block, wait for `done`, then re-run the `check` before continuing —
   never fake a signup, a dashboard click, or a secret paste.
3. **Route to the deep-dives** under `../skills/infra-setup/references/` and to the canonical
   `docs/` sections for fine print. Don't duplicate them.
4. **Stop at the done signal** in SKILL.md and hand back to `CONTRIBUTING.md`.

If `$ARGUMENTS` names a phase or provider (e.g. `cloudflare`, `phase 3`), jump straight to
that phase after the resume scan.
