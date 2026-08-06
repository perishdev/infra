# Operational decisions & live resource facts

Decisions and concrete resource facts specific to the perish.dev deployment.
The *procedure* for how any of this is done lives in the [infra-copilot plugin](https://github.com/hasansezertasan/infra-copilot); this file records what was decided and what exists for THIS infra.

## Cloudflare import scope (first bootstrap)

- The six Email-Routing DNS records on `perish.dev` were imported under Terraform via `cf-terraforming` (see the plugin's import reference for the how-to).
- The four GitHub Pages apex records and the `www` CNAME were written directly into [`terraform/cloudflare/dns.tf`](../terraform/cloudflare/dns.tf) — they had no prior existence to import.
- `cloudflare_pages_project` and `cloudflare_r2_bucket` were discovered during the first run but **deliberately excluded** from import: the Pages projects were unrelated personal repos and the R2 bucket was empty. **Scope decision: this repo manages perish.dev infra, not the whole Cloudflare account.**

## Live resource IDs (re-derivable via the HCP API; cached here for convenience)

- HCP org: `perishdev`
- Workspace `cloudflare`: `ws-WWKeFPiCAjV4STNX`
- Workspace `github-org`: `ws-iZFBsNEsUfJPRJ1Q`
- HCP status-check id (embedded in branch protection): `repo-id-CffUfWW6H1x6Bauq` — also set in [`.claude/infra-copilot.local.md`](../.claude/infra-copilot.local.md) and [`terraform/github/branch_protection.tf`](../terraform/github/branch_protection.tf). If the GitHub↔HCP connection is ever rebuilt this string changes and branch protection will silently block PRs until it is updated in both places.
