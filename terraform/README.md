# terraform/

Terraform code, organized as **one leaf directory per HCP Terraform workspace**. Each leaf is a self-contained root module with its own `versions.tf` (declaring the `cloud {}` block), `providers.tf`, `variables.tf`, and the resource files.

## Layout

```
terraform/
  cloudflare/                       -> HCP workspace: cloudflare
    versions.tf                     terraform / provider / cloud block
    providers.tf                    cloudflare provider config
    variables.tf                    sensitive vars only (api token)
    main.tf                         locals + zone import
    dns.tf                          all DNS records (email + GH Pages)
  github/                           -> HCP workspace: github-org
    versions.tf
    providers.tf                    github app auth
    variables.tf                    sensitive vars (app id, installation id, pem)
    main.tf                         placeholder
    repos.tf                        repository resources (infra, landing page)
    branch_protection.tf            main protection on both repos
    labels.tf                       safe-to-plan label
```

There is no per-environment split today:

- **Cloudflare**: one apex domain, one Cloudflare account. Staging surfaces (e.g. `staging.<domain>`, `app-staging` Worker) would live as additional resources inside the same workspace. Split into `cloudflare/{production,staging}/` only when we add a second apex domain dedicated to staging or move staging into a separate Cloudflare account.
- **GitHub**: the org is the org. No staging variant exists.

## Why one workspace per leaf

- A `terraform apply` for one concern can never touch another's state, even by accident — different workspaces, different state, different (sensitive) credentials.
- HCP's VCS integration filters by path (`terraform/<leaf>/**`), so a PR that only touches one leaf only triggers that workspace.
- One file per resource category inside each leaf keeps diff review focused.

## Adding a new workspace

1. Create `terraform/<concern>/` with `versions.tf`, `providers.tf`, `variables.tf`, and a resource file (`main.tf` or per-category `*.tf`).
2. Set the `cloud { workspaces { name = "<workspace-name>" } }` block in `versions.tf`.
3. Create the matching workspace in HCP under the `perishdev` org / `infra` project, VCS-linked to this repo, working directory set to the leaf dir, path filter `terraform/<concern>/**` (see [`../docs/setup.md`](../docs/setup.md) step 2 for the full per-workspace settings).
4. Populate sensitive variables (provider tokens, credentials) in HCP.
5. If protected status checks live on `main`, add the new workspace's check name to [`github/branch_protection.tf`](./github/branch_protection.tf) in the same PR.
6. Open a PR; the `safe-to-plan` label gates fork-PR plans (see [`../docs/ci.md`](../docs/ci.md)).

## What's not here

- `terraform/modules/` — reusable building blocks. Add when the same shape is needed in two places. Don't pre-build.
- An HCP-managing workspace (i.e. Terraform managing the HCP workspaces themselves via the `tfe` provider). Considered, deferred — the manual workspace setup is documented in [`../docs/setup.md`](../docs/setup.md) and runs once.

See also: [`../docs/secrets.md`](../docs/secrets.md), [`../docs/state.md`](../docs/state.md), [`../docs/ci.md`](../docs/ci.md), [`../docs/import.md`](../docs/import.md).
