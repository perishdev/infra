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

## Conventions

### `.terraform.lock.hcl` is committed

The lock file pins provider versions across team members and CI. It's the difference between "my laptop and the HCP runner see the same provider build" and "subtle drift surfaces on next `terraform init`." Always commit it; update it deliberately via `terraform init -upgrade`.

### Resource label naming

Lowercase snake_case, scoped enough to be unambiguous within the leaf. Examples already in the tree:

- `cloudflare_dns_record.mx_route1` (purpose + index)
- `cloudflare_dns_record.apex_gh_pages_1` (target + index, since there are four)
- `cloudflare_dns_record.dkim_cf2024_1` (selector + version)
- `github_repository.infra` (just the name; only one of it)

Avoid labels like `terraform_managed_resource_<hash>_<index>` (the default output of `cf-terraforming`). Rename before opening a PR.

### One file per category per leaf

Inside each leaf:

- `versions.tf`, `providers.tf`, `variables.tf`, `main.tf` are the standard skeleton.
- Resource files split by category, named for the noun: `dns.tf`, `repos.tf`, `branch_protection.tf`, `labels.tf`.
- Open a new file when a single resource type would exceed ~50 lines OR when a logical grouping wants its own header comment.

Avoid one giant `main.tf` per leaf. Avoid one file per resource (too granular).

### Provider version pinning

Pin to a major version with `~> X.Y` in `versions.tf`. `~> 5.0` allows `5.x` upgrades but blocks `6.0`. Allows automatic patch + minor updates on re-init; flags major version bumps as deliberate work.

Pure `>=` pins (`>= 5.0`) are too permissive — `terraform init` could pick up a breaking 6.x change without warning. Exact pins (`= 5.21.1`) are too tight — every patch release becomes a PR.

When bumping a major, follow the recipe in [`../docs/recipes.md`](../docs/recipes.md#bump-a-provider-version-safely).

### Cross-leaf references

Direct `data "..." "..." {}` between workspaces isn't supported until the `tfe` provider arc lands (see [Issue #8](https://github.com/perishdev/infra/issues/8)). Until then, hard-code IDs with a comment pointing at the source leaf, OR use `tfe_outputs` once available.

## What's not here

- `terraform/modules/` — reusable building blocks. Add when the same shape is needed in two places. Don't pre-build.
- An HCP-managing workspace (i.e. Terraform managing the HCP workspaces themselves via the `tfe` provider). Considered, deferred — the manual workspace setup is documented in [`../docs/setup.md`](../docs/setup.md) and runs once. See [Issue #8](https://github.com/perishdev/infra/issues/8).

See also: [`../docs/secrets.md`](../docs/secrets.md), [`../docs/state.md`](../docs/state.md), [`../docs/ci.md`](../docs/ci.md), [`../docs/import.md`](../docs/import.md), [`../docs/recipes.md`](../docs/recipes.md).
