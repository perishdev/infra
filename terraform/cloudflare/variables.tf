variable "cloudflare_api_token" {
  description = "Cloudflare API token. Supplied as a sensitive workspace variable in HCP Terraform; never set in this file."
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID. Not a secret."
  type        = string
}
