# Cloudflare resources.
#
# Identifiers (account_id, zone_id, apex domain) are non-credentials and live
# here as locals for readability — see docs/secrets.md "Things that look like
# secrets but aren't." The sensitive API token lives in HCP Terraform as a
# workspace variable and is consumed via var.cloudflare_api_token.

locals {
  domain     = "perish.dev"
  account_id = "d8a72309e747515805b614574ea7f323"
  zone_id    = "78ff9bdc9f1a38c01a935d3d079b1e7b"
}

# The zone already exists; import it so Terraform manages it without
# attempting to create a new one on the first apply.
import {
  to = cloudflare_zone.this
  id = local.zone_id
}

resource "cloudflare_zone" "this" {
  account = { id = local.account_id }
  name    = local.domain
  type    = "full"
}

# Records, R2 buckets, Pages projects, and other resources are brought
# under Terraform management via Cloudflare's `cf-terraforming` CLI —
# see docs/import.md for the runbook. Generated HCL lands in
# terraform/cloudflare/generated.tf for review and commit.
