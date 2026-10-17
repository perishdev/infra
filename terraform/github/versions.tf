terraform {
  required_version = ">= 1.9.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }

  # State lives in R2 (Cloudflare's S3-compatible store); plans and applies run in
  # GitHub Actions (.github/workflows/terraform-{plan,apply}.yml). See "Terraform CI
  # migration" in .infra-copilot/decisions.md. Credentials come from
  # AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY, never from this file.
  backend "s3" {
    bucket = "perishdev-tfstate"
    key    = "github/terraform.tfstate"
    region = "auto"
    endpoints = {
      s3 = "https://d8a72309e747515805b614574ea7f323.r2.cloudflarestorage.com"
    }

    # R2 implements conditional PutObject (If-None-Match), which the lockfile needs.
    use_lockfile = true

    # R2 is not AWS: no STS, no IMDS, no AWS region list, and it rejects the
    # SDK's default trailing checksums.
    use_path_style              = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
  }
}
