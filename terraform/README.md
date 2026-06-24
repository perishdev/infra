# terraform/

Terraform code, organized as **one leaf directory per HCP Terraform workspace**. Each leaf is a self-contained root module with its own `versions.tf` (declaring the `cloud {}` block), `providers.tf`, `variables.tf`, and `main.tf`.

## Layout

```
terraform/
  cloudflare/   -> HCP workspace: cloudflare
  github/       -> HCP workspace: github-org
```

There is no per-environment split today:

- **Cloudflare**: we manage a single apex domain in a single Cloudflare account. Staging surfaces (e.g. `staging.<domain>`, `app-staging` Worker) live as additional resources inside the same zone, in the same workspace. Split into `cloudflare/{production,staging}/` only when we add a second apex domain dedicated to staging or move staging into a separate Cloudflare account.
- **GitHub**: the org is the org. No staging variant exists.

## Why one workspace per leaf

- A `terraform apply` for one concern can never touch another concern's state, even by accident — different workspaces, different state, different (sensitive) credentials.
- HCP's VCS integration triggers exactly one run per workspace per push, so blast radius is bounded.
- Mirrors the convention in [`pypi/infra`](https://github.com/pypi/infra) and aligns with the environment separation rule in the top-level `CLAUDE.md`.

## Adding a new workspace

1. Create `terraform/<concern>/` (or `terraform/<concern>/<env>/` if a real isolation boundary justifies the split) with `versions.tf`, `providers.tf`, `variables.tf`, `main.tf`.
2. Set the `cloud { workspaces { name = "<workspace-name>" } }` block in `versions.tf`.
3. Create the matching workspace in HCP Terraform under the `perishdev` org, VCS-linked to this repo, working directory set to the leaf dir.
4. Populate sensitive variables (provider tokens, app credentials) as workspace variables in HCP, marked `sensitive`.
5. Open a PR; the `safe-to-plan` label gates fork-PR plans (see [`../docs/ci.md`](../docs/ci.md)).

## What's not here yet

- `terraform/modules/` — reusable building blocks. Add when the second resource needs the same shape in two places. Don't pre-build.
- Real resources. The current files are scaffolding; they declare providers and variables but create nothing.

See also: [`../docs/secrets.md`](../docs/secrets.md), [`../docs/state.md`](../docs/state.md), [`../docs/ci.md`](../docs/ci.md).
