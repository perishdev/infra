# Recipes

Common-task recipes. Each one is a step-by-step for a task you'll do more than once. The first time you do something is research; the second time on, find the recipe.

If you're about to write a recipe that isn't here, write it down after.

---

## Add a new DNS record to `perish.dev`

**Where it goes:** [`terraform/cloudflare/dns.tf`](../terraform/cloudflare/dns.tf).

**Steps:**

1. Branch off main: `git checkout -b feat/dns-<name>`.
2. Append a new `cloudflare_dns_record` block to `dns.tf`. Pick a section that matches the record's purpose (email routing vs. apex/GitHub Pages vs. a new section).
   ```hcl
   resource "cloudflare_dns_record" "<unique_label>" {
     zone_id  = local.zone_id
     type     = "TXT"           # or A, AAAA, CNAME, MX, ...
     name     = "<subdomain>.${local.domain}"  # use local.domain for the apex
     content  = "<value>"
     proxied  = false           # true only for A/AAAA/CNAME at the apex / proxied subdomains
     ttl      = 1               # 1 = auto when proxied; otherwise pick a number
     tags     = []
     settings = {}
   }
   ```
3. `terraform fmt terraform/cloudflare/`; commit; push; open PR.
4. HCP speculative plan should show `1 to add, 0 to change, 0 to destroy`.
5. Merge; confirm apply.

**Pitfalls:**
- `proxied = true` requires the record type to be A, AAAA, or CNAME, AND the target to be a real origin reachable by Cloudflare's edge. For text records, MX, SPF/DKIM/DMARC, keep `proxied = false`.
- A and CNAME at the same name are mutually exclusive per DNS spec — Cloudflare will reject. Delete one type before adding the other.
- For DKIM TXT records, escape the embedded double-quotes: `content = "\"v=DKIM1; ...\""`.

---

## Add a new GitHub repo to the org

**Where it goes:** [`terraform/github/repos.tf`](../terraform/github/repos.tf), [`terraform/github/branch_protection.tf`](../terraform/github/branch_protection.tf).

**Steps:**

1. Branch off main: `git checkout -b feat/repo-<name>`.
2. Add a `github_repository` block (no `import` block needed if you're creating the repo via Terraform):
   ```hcl
   resource "github_repository" "<short_label>" {
     name        = "<repo-name>"
     description = "..."
     visibility  = "public"  # or "private"
     topics      = ["..."]

     has_issues       = true
     has_projects     = false
     has_wiki         = false

     allow_squash_merge          = true
     allow_merge_commit          = false
     allow_rebase_merge          = false
     delete_branch_on_merge      = true
     squash_merge_commit_title   = "COMMIT_OR_PR_TITLE"
     squash_merge_commit_message = "COMMIT_MESSAGES"
   }
   ```
3. Add a `github_branch_protection` block for `main` in `branch_protection.tf` — copy `landing_page_main` if you don't need required status checks, or `infra_main` if you do.
4. `terraform fmt terraform/github/`; commit; push; open PR.
5. HCP plan: `1 to add` (or 2 if you added protection too).
6. Merge; confirm apply.

**Pitfalls:**
- New repos default to a single `main` branch with no commits. If you want to push to it immediately, the `auto_init = true` argument creates an initial commit. But: that bypasses your usual "first PR" flow on the new repo — easier to clone, push a `chore: initial commit`, then PR from there.
- `github_repository.<label>.node_id` (not `.id`) is what `github_branch_protection.repository_id` takes.
- If the repo will use GitHub Pages, configure `pages` in the `github_repository` block — or do it via the API after creation (the provider's `pages` support has gaps).

---

## Add a new label to `perishdev/infra`

**Where it goes:** [`terraform/github/labels.tf`](../terraform/github/labels.tf).

**Steps:**

1. Branch off main: `git checkout -b feat/label-<name>`.
2. Append:
   ```hcl
   resource "github_issue_label" "<short_label>" {
     repository  = github_repository.infra.name
     name        = "<label-name>"
     color       = "<6-hex>"  # without leading #
     description = "What the label means in 1 sentence."
   }
   ```
3. `terraform fmt`; commit; push; PR.
4. HCP plan: `1 to add`. Merge; confirm apply.

**Pitfalls:**
- Label colors are 6-hex without the `#`. Cloudflare and other systems use the `#`; GitHub doesn't.
- Names with spaces work, but URL-encoding them in PR queries (e.g. `is:pr label:"safe to plan"`) is uglier than `safe-to-plan`.

---

## Bump a provider version safely

**When:** a CVE notice, a new resource type you want, or routine version maintenance.

**Steps:**

1. Branch off main.
2. Find the provider in the relevant `versions.tf`. Bump:
   ```hcl
   cloudflare = {
     source  = "cloudflare/cloudflare"
     version = "~> 5.0"          # change to "~> 5.21" or "~> 6.0"
   }
   ```
3. From the leaf: `terraform init -upgrade`. This re-reads the provider, may update `.terraform.lock.hcl`.
4. `terraform fmt` and `terraform plan` locally.
5. Read the provider's CHANGELOG for the version range you crossed. Note any deprecated or removed resources.
6. Commit `versions.tf` AND the updated `.terraform.lock.hcl` (both should be in the diff).
7. PR; HCP speculative plan should be `no changes` if it's a pure version bump.

**Pitfalls:**
- If the provider's major version changes (e.g. `5.x` → `6.x`), expect resource schema changes. Read the upgrade guide before bumping.
- A version bump that introduces *no* code changes but shows a `~> change` in the plan usually means the new provider version generates state for a previously-computed attribute differently. Read the diff carefully — usually it's a no-op annotated.
- `terraform init -upgrade` is what touches the lock file. `terraform init` alone won't.

---

## Make a change that touches both workspaces

**When:** e.g. adding a Cloudflare resource that the GitHub workspace needs to know about (rare, but happens with cross-references like `output` → consumer workspace).

**Decision:** open one PR or two?

- **One PR**: simpler review, but the HCP plans on both workspaces run from the same commit. If one fails, the other still applies — partial-state risk. Use when the changes are *independent* (no ordering dependency) and rolling back one is fine.
- **Two PRs, sequenced**: open the producer PR first, merge + apply, then the consumer PR. Use when there's an ordering dependency (consumer reads producer's output).

**Steps for two PRs (the safer pattern):**

1. PR 1: change `terraform/cloudflare/` only. Merge + apply.
2. PR 2: change `terraform/github/` only, referencing the new Cloudflare output via `data` source or hardcoded ID. Merge + apply.

**Pitfalls:**
- HCP workspaces can't currently `data` source each other directly. To pass a value from one to another, either use `tfe_outputs` (when the HCP-as-code arc lands — see [Issue #8](https://github.com/perishdev/infra/issues/8)) or hardcode the value with a comment pointing at its source.
- "Both workspaces in one PR" PRs are noisier to review because the diff spans two concerns. Bias toward splitting unless the changes are genuinely atomic.

---

## When a recipe should become a module

A recipe is a copy-paste pattern; a module is shared code. Move a recipe into a module when:
- You've used it three or more times (the rule of three).
- The customization between uses is small (a few variables) compared to the boilerplate.
- The pattern is stable enough that you'd rather change it in one place than three.

For this repo today, nothing yet meets that bar. The first candidate when it does will probably be the standard "github_repository + branch_protection" pair.
