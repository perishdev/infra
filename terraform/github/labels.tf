# Issue / PR labels.
#
# `safe-to-plan` is the maintainer-applied label that lets HCP Terraform run a
# speculative plan on a PR from a fork (per docs/ci.md). Without this label,
# fork PRs only get GitHub Actions lint/validate, never see workspace
# variables, and produce no HCP plan.

resource "github_issue_label" "infra_safe_to_plan" {
  repository  = github_repository.infra.name
  name        = "safe-to-plan"
  color       = "0e8a16"
  description = "Maintainer has reviewed this fork PR; HCP may run a speculative plan."
}
