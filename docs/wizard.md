# Setup wizard (agent-first)

An **agent-runnable** bootstrap for this repo. Written for an AI agent (Claude Code,
opencode, codex, …) to execute end-to-end, pausing only for the steps a human
irreducibly must do.

If you are a human: hand this file to your agent and say *"run the setup wizard in
`docs/wizard.md`."* You'll be pinged when a browser click or a credential is needed.

> This wizard **orchestrates**; it does not duplicate. The authoritative per-step
> detail lives in [`setup.md`](./setup.md) (bootstrap) and [`import.md`](./import.md)
> (Cloudflare migration). The wizard adds the *actor split* and the *resume protocol*
> on top. When a step says "see `setup.md#3`", read that section for the fine print.

---

## The one idea

**The human is the browser and the keyholder. Everything scriptable is the agent's.**

There is exactly one thing a human must do that an agent cannot: sit in front of a
browser, sign up for a SaaS, and mint the first credential. After that first
credential exists (an HCP token from `terraform login`), the agent can create
workspaces, set variables, read plans, and confirm applies **over the HCP API** —
no more clicking.

So the wizard shrinks the human surface to three kinds of action:

1. **Sign up** for a service (browser-only).
2. **Mint a credential** in a dashboard (browser-only — no API to bootstrap the first token).
3. **Paste a secret** into HCP (browser-only, because the agent must never see the plaintext).

Everything else — verifying, creating workspaces, importing existing resources,
running the first plan — is the agent's job.

---

## Actors

Every step is tagged with who performs it:

| Tag | Meaning | Agent behaviour |
|---|---|---|
| **`AGENT`** | The agent runs it (shell, `gh`, `terraform`, HCP API). | Execute. Verify with the step's `check`. Continue on green. |
| **`HUMAN`** | Irreducibly human (signup, dashboard, secret paste). | **Stop.** Emit the handoff block below. Wait for the human to reply `done`. Then run the `check` to confirm before continuing. |

### The handoff block

When a step is `HUMAN`, the agent must **not** guess or fake it. It stops and prints a
block in exactly this shape, then waits:

```
┌─ HUMAN ACTION NEEDED ─────────────────────────────
│ Step:   <id> — <title>
│ Why:    <one line — what this unblocks>
│ Do this:
│   1. <precise, copy-pasteable instruction, with URL>
│   2. …
│ When done, reply "done" and I'll verify.
└───────────────────────────────────────────────────
```

After the human replies, the agent runs the step's `check` (see
[`setup.steps.yaml`](./setup.steps.yaml)). If the check fails, the agent re-emits the
handoff with what it observed — it never silently proceeds past a red check.

---

## Resume protocol

The wizard is **idempotent and resumable**. On every run, before doing anything, the
agent walks [`setup.steps.yaml`](./setup.steps.yaml) top to bottom and runs each
step's `check` to discover *where setup already is*. It resumes at the first step
whose check is red. A finished repo produces all-green and the agent reports "already
set up, nothing to do."

```text
for step in setup.steps.yaml:
    if run(step.check) is green:  skip, print "✓ {step.id}"
    else:                         this is where we resume
```

Never assume state from memory or a previous session — always re-check.

---

## Preflight (AGENT)

Confirm the agent's toolbox before starting. All of these are the agent's to install
if missing (via `brew`, the platform package manager, etc.) — none require a human.

```sh
terraform version      # ≥ 1.9   — provisioning + import blocks
gh --version           # GitHub CLI — repo ops, Pages, App install checks
jq --version           # JSON wrangling for HCP/Cloudflare/GitHub APIs
curl --version         # HCP + Cloudflare REST
```

Then detect the credential the whole wizard pivots on:

```sh
# Is there already an HCP token on this machine?
jq -re '.credentials["app.terraform.io"].token' ~/.terraform.d/credentials.tfrc.json \
  && echo "HCP token present — agent can drive the API" \
  || echo "No HCP token yet — first HUMAN step will mint one"
```

---

## Phases

Run in order. Each phase links to the provider deep-dive under
[`providers/`](./providers/) and to the canonical section of `setup.md`.

| # | Phase | Actors | Deep dive |
|---|---|---|---|
| 0 | **HCP bootstrap** — sign up, `terraform login`, get the pivot token | `HUMAN` then `AGENT` | [`setup.md#1`](./setup.md#1-hcp-terraform--organization), [`state.md`](./state.md) |
| 1 | **HCP workspaces** — create `cloudflare` + `github-org`, set VCS + safety toggles | `AGENT` (API) with `HUMAN` VCS OAuth | [`setup.md#2`](./setup.md#2-hcp-terraform--workspaces) |
| 2 | **Cloudflare** — mint scoped token, paste into HCP, verify | `HUMAN` mint/paste, `AGENT` verify | [`providers/cloudflare.md`](./providers/cloudflare.md) |
| 3 | **GitHub** — create + install the GitHub App, paste creds into HCP | `HUMAN` create/install/paste, `AGENT` verify | [`providers/github.md`](./providers/github.md) |
| 4 | **First plan** — `init` + speculative `plan` per leaf, read via API | `AGENT` | [`setup.md#6`](./setup.md#6-local-development) |
| 5 | **Migration** — adopt existing resources with import blocks (no re-create) | `AGENT` run, `HUMAN` mint discovery token | [`providers/migration.md`](./providers/migration.md) |
| 6 | **GCP** *(optional, template only)* — not provisioned today | design decision first | [`providers/gcp.md`](./providers/gcp.md) |

### Phase 0 — HCP bootstrap

The only unavoidable cold-start. Produces the token that lets the agent script the rest.

- **`HUMAN` — hcp-signup.** Sign up at <https://app.terraform.io/>, create org
  **`perishdev`**, create project **`infra`**. (Org name must equal the `organization`
  field in every `terraform/*/versions.tf` — it does: `perishdev`.)
- **`HUMAN` — hcp-login.** Run `terraform login` locally (it opens a browser and asks
  HCP for a user API token). This is `HUMAN` because it needs an interactive browser —
  but it's the *last* time a human touches the terminal for auth. Token lands in
  `~/.terraform.d/credentials.tfrc.json`.
- **`AGENT` — hcp-verify.** From here the agent owns the HCP API:
  ```sh
  HCP_TOKEN=$(jq -r '.credentials["app.terraform.io"].token' ~/.terraform.d/credentials.tfrc.json)
  curl -sf "https://app.terraform.io/api/v2/organizations/perishdev" \
    -H "Authorization: Bearer $HCP_TOKEN" | jq -e '.data.id' \
    && echo "✓ HCP org reachable"
  ```

### Phase 1 — HCP workspaces

Two workspaces, one per leaf. The agent creates them via API; a human does the one-time
GitHub↔HCP OAuth connection (browser).

| Workspace | Leaf | VCS working dir | Path filter | Auto-apply |
|---|---|---|---|---|
| `cloudflare` | `terraform/cloudflare/` | `terraform/cloudflare` | `terraform/cloudflare/**` | **no** |
| `github-org` | `terraform/github/` | `terraform/github` | `terraform/github/**` | **no** |

- **`HUMAN` — vcs-connect.** In HCP → org Settings → VCS Providers, connect GitHub via
  OAuth, scoped to this repo only. (Browser-only OAuth handshake.)
- **`AGENT` — workspaces-create.** Create both workspaces via the HCP API with the
  correct working directory, path-based run triggering, remote execution, and
  auto-apply **off**. The safety toggles that matter — and *why each one bites if wrong*
  — are spelled out in [`setup.md#2`](./setup.md#2-hcp-terraform--workspaces): speculative
  plans **on**, path-scoped triggers, and — set in the UI — **fork** speculative plans
  **off**. Ready-to-run (idempotent — a 422 means the workspace already exists, treat as
  ✓):

  ```sh
  export HCP_TOKEN=$(jq -r '.credentials["app.terraform.io"].token' ~/.terraform.d/credentials.tfrc.json)
  ORG=perishdev
  REPO=perishdev/infra                       # the repo HCP watches via VCS

  # oauth-token-id from the VCS connection created in the vcs-connect step
  OAUTH_TOKEN_ID=$(curl -sf "https://app.terraform.io/api/v2/organizations/$ORG/oauth-clients" \
    -H "Authorization: Bearer $HCP_TOKEN" \
    | jq -r '.data[0].relationships["oauth-tokens"].data[0].id')

  # Build the JSON:API payload with `jq -n` (no heredoc; safe to copy-paste, correct quoting)
  create_ws () {  # $1 = workspace name   $2 = working directory
    jq -n --arg name "$1" --arg dir "$2" --arg repo "$REPO" --arg tok "$OAUTH_TOKEN_ID" '
      {data:{type:"workspaces",attributes:{
        name:$name, "working-directory":$dir, "execution-mode":"remote",
        "auto-apply":false, "speculative-enabled":true, "file-triggers-enabled":true,
        "trigger-patterns":[$dir+"/**"], "queue-all-runs":false, "global-remote-state":false,
        "vcs-repo":{identifier:$repo, "oauth-token-id":$tok, branch:"main"}}}}' \
    | curl -sf -X POST "https://app.terraform.io/api/v2/organizations/$ORG/workspaces" \
        -H "Authorization: Bearer $HCP_TOKEN" \
        -H "Content-Type: application/vnd.api+json" -d @- \
    | jq -r '"✓ " + .data.attributes.name + " created"'
  }

  create_ws cloudflare terraform/cloudflare
  create_ws github-org  terraform/github
  ```

  > `trigger-patterns` (glob) requires `file-triggers-enabled: true` — that pair is the
  > path-scoping toggle. `speculative-enabled: true` is the master switch for plans on PRs.
  > The **fork** speculative-plan toggle is *separate* and has no clean create-time
  > attribute — confirm it's **off** in the workspace's UI → Settings → Version Control
  > (it defaults off; the label-gated flow in [`ci.md`](./ci.md) replaces it for forks).

  Verify:
  ```sh
  for ws in cloudflare github-org; do
    curl -sf "https://app.terraform.io/api/v2/organizations/perishdev/workspaces/$ws" \
      -H "Authorization: Bearer $HCP_TOKEN" \
      | jq -e '.data.attributes["auto-apply"] == false' >/dev/null \
      && echo "✓ $ws exists, auto-apply off"
  done
  ```

> The end state of Phases 0–1 (HCP-as-clickops today) is tracked for future
> Terraform-ification in [Issue #8](https://github.com/perishdev/infra/issues/8).
> Until then these steps are API calls, not `.tf` files.

### Phase 2 — Cloudflare

The agent cannot mint a scoped Cloudflare token from nothing (bootstrap problem), and
must never see the plaintext. So minting and pasting are `HUMAN`; verifying is `AGENT`.
Full walkthrough: [`providers/cloudflare.md`](./providers/cloudflare.md).

- **`HUMAN` — cf-token.** Mint a Custom token (Zone·DNS·Edit, Zone·Settings·Edit for
  `perish.dev`), paste it into HCP → `cloudflare` workspace → var `cloudflare_api_token`
  (**Terraform** var, **Sensitive**). See [`setup.md#3`](./setup.md#3-cloudflare-api-token).
- **`AGENT` — cf-verify.** The agent can't read the redacted value, so it verifies
  *presence and shape*, then proves the token works by running a plan (Phase 4):
  ```sh
  WS_ID=$(curl -sf ".../workspaces/cloudflare" -H "Authorization: Bearer $HCP_TOKEN" | jq -r '.data.id')
  curl -sf "https://app.terraform.io/api/v2/workspaces/$WS_ID/vars" \
    -H "Authorization: Bearer $HCP_TOKEN" \
    | jq -e '.data[] | select(.attributes.key=="cloudflare_api_token") | .attributes.sensitive==true' \
    && echo "✓ cloudflare_api_token present and sensitive"
  ```

### Phase 3 — GitHub

The `github-org` workspace authenticates as a **GitHub App**, not a PAT. App creation
and installation are browser flows; the three credentials get pasted into HCP. Full
walkthrough incl. the manifest-flow shortcut: [`providers/github.md`](./providers/github.md).

- **`HUMAN` — gh-app.** Create the App under `perishdev`, install it scoped to
  `perishdev/infra` + `perishdev/perishdev.github.io`, paste `github_app_id`,
  `github_app_installation_id`, `github_app_pem` (full PEM incl. BEGIN/END lines) into
  the `github-org` workspace as sensitive vars. See [`setup.md#4`](./setup.md#4-github-app).
- **`AGENT` — gh-verify.** Confirm all four vars exist (`github_owner` +
  the three App creds), then prove them with a plan in Phase 4.

### Phase 4 — First plan (AGENT)

Now the agent proves every credential end-to-end. For each leaf:

```sh
cd terraform/cloudflare        # then repeat for terraform/github
terraform init                 # authenticates to HCP automatically
terraform plan                 # speculative run in HCP; output streams back
```

A VCS-connected workspace **allows `plan` from the CLI but blocks `apply`** — that gate
is intentional (apply happens on merge to `main`, confirmed by a human or an
authenticated API call). Read the plan without the UI via the HCP API toolkit in
[`hcp-api.md`](./hcp-api.md). Green plans on both leaves = credentials proven.

### Phase 5 — Migration (adopt existing resources)

If the domain / repos already exist (they do for `perish.dev`), **import** them so
Terraform manages them without recreating. The agent runs `cf-terraforming` and writes
`import` blocks; a human mints the short-lived read-only discovery token. Canonical
runbook: [`import.md`](./import.md); cross-provider generalisation:
[`providers/migration.md`](./providers/migration.md).

The success signal is unambiguous: `terraform plan` shows every existing resource as
**"will import"**, nothing as **"will create"**.

### Phase 6 — GCP (template, optional)

**Not provisioned today.** GCP is not a managed provider in this repo. Adopting it is a
**locked-design-decision change** — update `CLAUDE.md` and `terraform/README.md` first,
then follow the same actor split. Template: [`providers/gcp.md`](./providers/gcp.md).

---

## Done signal

Setup is complete when the agent reports:

- ✓ HCP org `perishdev` + project `infra` reachable via API.
- ✓ Workspaces `cloudflare` and `github-org` exist, VCS-linked, auto-apply off, fork
  speculative plans off.
- ✓ All sensitive vars present (`cloudflare_api_token`; `github_app_id`,
  `github_app_installation_id`, `github_app_pem`).
- ✓ `terraform plan` green on both leaves.
- ✓ Existing resources imported (plan shows imports, no creates) — if migrating.

At that point day-to-day work follows [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Porting to another organization

This wizard is written concretely for **`perishdev` / `perish.dev`**. To reuse it as
groundwork for a different org, change these — and nothing else:

| Token in the docs | Meaning | Where it appears |
|---|---|---|
| `perishdev` | HCP org **and** GitHub org slug | `terraform/*/versions.tf` (`organization`), every HCP API URL, App install URL, workspace names' `-org` suffix |
| `perish.dev` | apex domain | `terraform/cloudflare/main.tf` (`local.domain`), Cloudflare token/zone scoping |
| `d8a72309…` | Cloudflare **account ID** | `terraform/cloudflare/main.tf` (`local.account_id`) |
| `78ff9bdc…` | Cloudflare **zone ID** | `terraform/cloudflare/main.tf` (`local.zone_id`), migration commands |
| `perishdev/infra`, `perishdev/perishdev.github.io` | managed repos | `terraform/github/repos.tf`, App install scope |
| `repo-id-CffUfWW6H1x6Bauq` | per-installation HCP status-check ID | `terraform/github/branch_protection.tf` — **regenerated by HCP**, not chosen; see [`ci.md`](./ci.md) |

Porting checklist for the agent:

1. `grep -rn 'perishdev\|perish\.dev\|d8a72309\|78ff9bdc' terraform/ docs/` to enumerate every literal.
2. Replace the org/domain/repo literals with the new org's values.
3. Re-derive the two Cloudflare IDs from the new account (`AGENT` can read them via the
   Cloudflare API once the new token exists; see [`providers/cloudflare.md`](./providers/cloudflare.md)).
4. Leave `repo-id-…` alone — it is emitted by HCP when the new VCS connection is made,
   and copied into `branch_protection.tf` *after* Phase 1. Never invent it.
5. Re-run the wizard from Phase 0. The resume protocol handles the rest.
