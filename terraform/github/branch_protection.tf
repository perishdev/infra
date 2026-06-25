# Branch protection on `main` for each repo.
#
# The required status check names must match exactly what GitHub displays on
# a PR. If a check is renamed, branch protection blocks PRs until the rule is
# updated — accept the friction in exchange for catching renames early.

resource "github_branch_protection" "infra_main" {
  repository_id = github_repository.infra.node_id
  pattern       = "main"

  enforce_admins                  = false # admin can bypass for emergencies
  require_signed_commits          = false
  required_linear_history         = true
  require_conversation_resolution = true
  allows_force_pushes             = false
  allows_deletions                = false

  required_status_checks {
    strict = true # branch must be up-to-date with main before merge
    contexts = [
      "terraform fmt",
      "terraform validate (terraform/cloudflare)",
      "terraform validate (terraform/github)",
      # The HCP check name includes the per-installation VCS-repo ID. If
      # the GitHub connection in HCP is ever recreated, this string changes
      # and this rule must be updated.
      "Terraform Cloud/perishdev/repo-id-CffUfWW6H1x6Bauq",
    ]
  }
}

resource "github_branch_protection" "landing_page_main" {
  repository_id = github_repository.landing_page.node_id
  pattern       = "main"

  enforce_admins                  = false
  required_linear_history         = true
  require_conversation_resolution = true
  allows_force_pushes             = false
  allows_deletions                = false

  # No CI on the landing page repo today, so no required status checks.
  # Add when/if a build workflow is introduced.
}
