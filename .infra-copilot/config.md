---
# infra-copilot:customization start
backend: hcp
github_org: perishdev
apex_domain: perish.dev
cloudflare_account_id: d8a72309e747515805b614574ea7f323
cloudflare_zone_id: 78ff9bdc9f1a38c01a935d3d079b1e7b
# First entry is this repo — the checks read it as REPO.
managed_repos:
  - perishdev/infra
  - perishdev/perishdev.github.io
hcp_org: perishdev
hcp_status_check_id: repo-id-CffUfWW6H1x6Bauq
additional_providers: []
# infra-copilot:customization end
---

# infra-copilot config — perishdev / perish.dev

Public identifiers for this repo, read by the
[infra-copilot plugin](https://github.com/hasansezertasan/infra-copilot) at startup.
Sensitive data never lives here.

`backend: hcp` holds until each leaf cuts over to R2 state and GitHub Actions; see
**Terraform CI migration** in [`decisions.md`](./decisions.md). The cutover switches this
to `backend: object-storage` and drops the `hcp_*` fields.

Keep the two `infra-copilot:customization` comments: a re-scaffold preserves everything
between them verbatim, and stops rather than guessing if they are missing or unbalanced.
