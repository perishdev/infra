# infra-copilot decisions

Durable provider, authentication, state, and safety choices for this repository.
Migrated from the locked-decisions table that used to live in [`CLAUDE.md`](../CLAUDE.md).
Change a row deliberately, in the same PR as the code it governs.

Keep the two `infra-copilot:customization` comments around the table: a re-scaffold
preserves everything between them verbatim, and stops rather than guessing if they are
missing or unbalanced.

<!-- infra-copilot:customization start -->

| Decision | Choice | Status | Rationale |
|---|---|---|---|
| Terraform backend | HCP Terraform, org `perishdev`, project `infra`, one workspace per leaf (`cloudflare`, `github-org`) | locked | Managed remote state and locking; no local `.tfstate`. To be superseded per leaf by **Terraform CI migration**. |
| Terraform-time secrets | HCP workspace variables (sensitive) | locked | Provider credentials never touch the repo. To be superseded per leaf by **Terraform CI credentials**. |
| CI-time secrets | None. The old table listed `TF_API_TOKEN`, but no repo secret exists and no workflow reads one. | locked | The fork-safe `fmt` / `validate` gates need no provider access. To be superseded by **Terraform CI credentials**. |
| GitHub auth | GitHub App, not a PAT | locked | Org-scoped, revocable, not tied to a person. |
| CI plan/apply policy | Plan on PR (collaborators automatically; fork PRs only after a maintainer adds `safe-to-plan`); apply gated to `main` plus manual confirmation in HCP | locked | Every apply is confirmed against a reviewed plan. To be superseded by **Terraform CI apply** and **Fork PRs**. |
| PR status checks | `fmt`, both `validate` jobs, and HCP's aggregated `Terraform Cloud/perishdev/repo-id-CffUfWW6H1x6Bauq` | locked | The `repo-id` changes whenever the GitHub↔HCP connection is rebuilt, silently blocking every PR until `terraform/github/branch_protection.tf` is updated. To be superseded by **Plan status check**. |
| At-rest encryption in repo | None: nothing encrypted is committed | locked | Anything sensitive lives in an external store, so there is no key to manage or leak. |
| Toolchain | Exact pins in `mise.toml` (`terraform`, `gh`, `jq`) plus a committed `mise.lock` with per-platform checksums | locked | Same binaries on every machine and in CI; `MISE_LOCKED=1` refuses anything off-lock. CI installs Terraform through `mise`, so `mise.toml` is the only CI pin. |
| Terraform version | `1.15.9`, from `mise.toml` | locked | While HCP runs plans, both workspaces carry the same version and are bumped together with `mise.toml`. After **Terraform CI migration**, `mise.toml` is the only pin. |
| Terraform CI migration | HCP → GitHub Actions, with state in the R2 bucket `perishdev-tfstate`, key `<leaf>/terraform.tfstate`, through Terraform's `s3` backend. Order: bootstrap (bucket and credentials), then one cutover PR per leaf, `github` then `cloudflare`, then HCP retirement. | proposed | Keeps everything on providers already in use (Cloudflare, GitHub) and drops HCP as a third vendor and login. A cutover PR may merge only after that leaf's state has been pushed to R2 and its HCP workspace locked; otherwise the first apply on `main` runs against empty state. Each cutover PR also rewrites what still assumes HCP: `required_status_checks` in `terraform/github/branch_protection.tf`, the leaf's `versions.tf`, and the docs. The R2 bucket is created by hand, not by the `cloudflare` leaf, which cannot safely own the bucket that holds its own state. Supersedes **Terraform backend**, **Terraform-time secrets**, **CI-time secrets**, **CI plan/apply policy**, and **PR status checks** as each leaf cuts over. |
| State locking | `use_lockfile = true`: a `.tflock` object written with a conditional `PutObject` (`If-None-Match`), which R2 supports. PR plans run `-lock=false`. Applies are serialised by workflow `concurrency`, never cancelled midway. | proposed | No DynamoDB-style lock table exists on R2. The plan credential is read-only, so it cannot take a lock, and plans do not need one. One apply at a time keeps the lockfile a backstop rather than the only guard. |
| State backups | After every apply, copy each leaf's state to `backups/<leaf>/<UTC timestamp>.tfstate` in the same bucket; a bucket lifecycle rule expires backups after 90 days. | proposed | R2 implements neither bucket versioning nor object lock, so a bad write or a deleted state object cannot otherwise be undone. |
| Terraform CI credentials | Read-only plan credentials as repo-level Actions secrets: `CLOUDFLARE_PLAN_API_TOKEN`, a read-only GitHub App, an R2 key with Object Read on the state bucket. Write credentials only as `terraform-<leaf>` environment secrets, deployable from `main` only: `CLOUDFLARE_API_TOKEN`, a write GitHub App, an R2 key with Object Read & Write on the state bucket. | proposed | Any branch's workflow can read repo-level secrets, so nothing at repo level may be able to write. Environment secrets reach only jobs running in that environment, and the environment admits only `main`. A read-only GitHub App may not see every attribute a refresh reads (merge settings need Contents: write), in which case github-leaf PR plans run `-refresh=false` against the last-applied state; confirm during the `github` cutover. |
| Terraform CI apply | Auto-apply on merge. Every push to `main` plans and applies every leaf (no path filter), each in its `terraform-<leaf>` environment with no required reviewer. The apply job refuses empty state and refuses any commit that is not `main`'s current tip. | proposed | The PR's reviewed plan is the approval. Environment required reviewers are available on this public repo and were deliberately not chosen. Accepted risks: drift between review and merge (kept small by `strict` branch protection), and drift made outside Terraform being reverted by the next merge, whichever leaf it touched, without a reviewed plan showing it. Supersedes the "production applies are never auto-applied" rule in `CLAUDE.md`. |
| Destructive apply opt-in | Every apply inspects its saved plan's JSON and refuses any action containing `delete` (destroys and both replacement orders) unless the merged PR that produced the commit carries the `allow-destroy` label. PR plan comments list deletes and replacements above the collapsed plan. | proposed | With auto-apply, nothing else stands between a merged mistake and a deleted zone or repo. `removed { lifecycle { destroy = false } }` is a `forget`, not a `delete`, and stays allowed. The label is an intent marker, not authorization: any writer can add it. |
| Plan status check | One required context, `plan`: an aggregate job in `terraform-plan.yml` that always reports and fails when any changed leaf's plan did not succeed. | proposed | Per-leaf jobs are path-filtered, and a required check that a filter skips never reports and blocks the PR forever. Unlike HCP's `repo-id` context, the job name does not change when a connection is rebuilt. |
| Fork PRs | `fmt` and `validate` only, no plan. | proposed | GitHub gives a fork's `pull_request` run no secrets, so a fork cannot plan; the `plan` job reports that as a failure for any leaf the fork changed, and a maintainer re-opens the change from a branch. Supersedes the `safe-to-plan` label flow. |
| Plan visibility | Plans are posted as PR comments and run summaries, public on this public repository. | proposed | HCP kept plan output behind an HCP login. Terraform redacts values marked sensitive; everything else these leaves manage (DNS records, repo settings) is already public. |

<!-- infra-copilot:customization end -->

Statuses:

- `proposed` — under discussion; workflows must not assume it.
- `locked` — authoritative until explicitly superseded.
- `superseded` — retained for history; link or name the replacement decision.

No secrets, tokens, private keys, or credentials in this file.
