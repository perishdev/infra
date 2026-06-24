terraform {
  required_version = ">= 1.9.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }

  cloud {
    organization = "perishdev"

    workspaces {
      name = "github-org"
    }
  }
}
