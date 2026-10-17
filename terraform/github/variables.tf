variable "github_owner" {
  description = "GitHub org or user this workspace manages."
  type        = string
}

variable "github_app_id" {
  description = "GitHub App ID. From a repo variable (plan App) or the terraform-github environment (apply App)."
  type        = string
  sensitive   = true
}

variable "github_app_installation_id" {
  description = "GitHub App installation ID for var.github_owner. Same source as github_app_id."
  type        = string
  sensitive   = true
}

variable "github_app_pem" {
  description = "GitHub App private key (PEM contents). A repo secret (plan App) or terraform-github environment secret (apply App); never committed."
  type        = string
  sensitive   = true
}
