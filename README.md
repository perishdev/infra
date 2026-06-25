# infra

There is dust in the clouds, infrastructure as code for perishdev.

## What this repo manages

- **Cloudflare** — the `perish.dev` zone, all DNS records (Email Routing + GitHub Pages), via the [`cloudflare/cloudflare`](https://registry.terraform.io/providers/cloudflare/cloudflare/latest) v5 Terraform provider.
- **GitHub** — `perishdev/infra` and `perishdev/perishdev.github.io` repo settings, branch protection on `main`, the `safe-to-plan` label, via the [`integrations/github`](https://registry.terraform.io/providers/integrations/github/latest) v6 Terraform provider.
- **HCP Terraform** — remote state, runs, and the workspace variables that hold the API credentials. The repo's own `terraform/cloud {}` block lives in each leaf's `versions.tf`.

No hosts of our own (no Salt, no Ansible). Everything in scope is SaaS-shaped.

## Where things live

```
terraform/
  cloudflare/   one HCP workspace (cloudflare),     zone + DNS
  github/       one HCP workspace (github-org),     repos + protection + labels
.github/
  workflows/    fork-safe terraform fmt + validate gates
docs/
  secrets.md    secrets store, GitHub App, rotation
  state.md      HCP backend, workspace layout
  ci.md         workflow contract, fork-PR policy
  setup.md      out-of-band bootstrap runbook
  import.md     cf-terraforming runbook for adopting existing Cloudflare state
```

For the contracts the repo is built on — secrets, state, CI — see [`CLAUDE.md`](./CLAUDE.md). For the live design decisions table, look there first.

## Contributing

Branch protection requires four green checks before any merge to `main`:

- `terraform fmt`
- `terraform validate (terraform/cloudflare)`
- `terraform validate (terraform/github)`
- `Terraform Cloud/perishdev/...` (the HCP aggregated commit status)

Fork PRs only get GitHub Actions; HCP plans require a maintainer to apply the `safe-to-plan` label first. See [`docs/ci.md`](./docs/ci.md) for the full policy.

Conventional Commits, Conventional Branches, Conventional PR titles.

## License

[MIT](./LICENSE)
