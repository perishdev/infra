variable "github_owner" {
  description = "GitHub org or user this workspace manages."
  type        = string
}

variable "github_app_id" {
  description = "GitHub App ID. Sensitive workspace variable in HCP Terraform."
  type        = string
  sensitive   = true
}

variable "github_app_installation_id" {
  description = "GitHub App installation ID for var.github_owner. Sensitive workspace variable in HCP Terraform."
  type        = string
  sensitive   = true
}

variable "github_app_pem" {
  description = "GitHub App private key (PEM contents). Sensitive workspace variable in HCP Terraform; never committed."
  type        = string
  sensitive   = true
}
