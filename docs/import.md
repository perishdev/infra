# Importing existing Cloudflare resources

Use Cloudflare's own [`cf-terraforming`](https://github.com/cloudflare/cf-terraforming) CLI to bring resources that already exist in the `perish.dev` zone (and the parent Cloudflare account) under Terraform management without recreating them.

Why not a custom script: cf-terraforming is maintained by Cloudflare alongside the Terraform provider, so import ID formats and HCL schemas track provider changes automatically. A hand-rolled script would drift.

## Install

```sh
brew tap cloudflare/cloudflare
brew install cloudflare/cloudflare/cf-terraforming
# or:
go install github.com/cloudflare/cf-terraforming/cmd/cf-terraforming@latest
```

## What it supports

Coverage is **broad but not total** for the v5 provider. As of cf-terraforming v0.27 (May 2026):

| Resource | Supported by `generate` |
|---|---|
| `cloudflare_dns_record` | yes |
| `cloudflare_r2_bucket` | yes |
| `cloudflare_pages_project` | yes |
| `cloudflare_workers_kv_namespace` | yes |
| `cloudflare_workers_custom_domain` | yes |
| `cloudflare_workers_cron_trigger` | yes (needs `--resource-id`) |
| `cloudflare_workers_script` | **no** — bundle content can't be round-tripped; define in the app repo |
| `cloudflare_workers_route` | **no** — define manually alongside the script |
| Zone settings (`cloudflare_zone_setting`) | yes (needs `--resource-id` listing each setting) |

For the script/route gap: Worker code typically lives in the app repo it serves, not in this infra repo. Importing the resource here would tie its state to an empty `content` field. Define the route + script in the app's own Terraform once that app exists.

## Generate HCL for the zone

```sh
export CLOUDFLARE_API_TOKEN=...        # token with read scopes for each resource type
export CLOUDFLARE_ZONE_ID=78ff9bdc9f1a38c01a935d3d079b1e7b
export CLOUDFLARE_ACCOUNT_ID=d8a72309e747515805b614574ea7f323

cd terraform/cloudflare

terraform init -backend=false          # cf-terraforming requires an initialised dir

# Zone-scoped resources (DNS records) — --account and --zone are mutually exclusive.
cf-terraforming generate \
  --terraform-binary-path "$(which terraform)" \
  --resource-type "cloudflare_dns_record" \
  --zone "$CLOUDFLARE_ZONE_ID" \
  > generated.tf

# Account-scoped resources.
cf-terraforming generate \
  --terraform-binary-path "$(which terraform)" \
  --resource-type "cloudflare_r2_bucket,cloudflare_pages_project,cloudflare_workers_kv_namespace" \
  --account "$CLOUDFLARE_ACCOUNT_ID" \
  >> generated.tf
```

Without `--terraform-binary-path`, cf-terraforming downloads its own terraform binary into the current directory. The flag tells it to reuse the one already on PATH.

`generated.tf` is the file the existing comment in `main.tf` references. Review it: rename resource labels to something readable (cf-terraforming uses `terraform_managed_resource` placeholders), drop anything you don't actually want managed, and commit.

## Emit `import` blocks

```sh
cf-terraforming import \
  --modern-import-block \
  --terraform-binary-path "$(which terraform)" \
  --resource-type "cloudflare_dns_record" \
  --zone "$CLOUDFLARE_ZONE_ID" \
  >> generated.tf

cf-terraforming import \
  --modern-import-block \
  --terraform-binary-path "$(which terraform)" \
  --resource-type "cloudflare_r2_bucket,cloudflare_pages_project,cloudflare_workers_kv_namespace" \
  --account "$CLOUDFLARE_ACCOUNT_ID" \
  >> generated.tf
```

`--modern-import-block` emits Terraform 1.5+ `import { to = ... id = "..." }` blocks rather than the legacy CLI commands. Append to the same file so resources and their imports stay co-located.

## Verify and apply

```sh
terraform fmt generated.tf
terraform validate
terraform plan      # expect: every existing resource shown as "will import", nothing as "will create"
```

If `plan` shows any `create` for a resource that already exists, the resource name or import ID in `generated.tf` is wrong — fix before applying.

Once the plan is clean, commit `generated.tf` and let HCP Terraform run the apply (manual confirmation per `docs/ci.md`).

## When to re-run

Re-run `cf-terraforming generate` whenever new resources appear in Cloudflare that you want Terraform to manage. The cleanest workflow is to write new resources directly in Terraform from the start; cf-terraforming is for one-time onboarding of legacy state, not steady-state operations.

> Note: cf-terraforming is **not** intended for use in CI. It runs locally during onboarding, output is reviewed by a human, then committed.
