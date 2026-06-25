# Repositories under perishdev/.
#
# Both repos already exist; `import` blocks adopt them into state without
# recreation. Settings are then asserted via the resource blocks below;
# anything we changed (description, merge strategies, has_projects, etc.)
# will appear as `update` actions on the first plan.

import {
  to = github_repository.infra
  id = "infra"
}

resource "github_repository" "infra" {
  name        = "infra"
  description = "@perishdev Infrastructure — Terraform-managed Cloudflare and GitHub config for perish.dev"
  visibility  = "public"
  topics      = ["terraform", "cloudflare", "infrastructure", "iac"]

  has_issues      = true
  has_projects    = false
  has_wiki        = false
  has_discussions = false

  # Squash-only merges. Subject line uses the PR title; body collapses the
  # individual commit messages (Conventional Commits stay readable).
  allow_squash_merge          = true
  allow_merge_commit          = false
  allow_rebase_merge          = false
  allow_auto_merge            = false
  delete_branch_on_merge      = true
  squash_merge_commit_title   = "COMMIT_OR_PR_TITLE"
  squash_merge_commit_message = "COMMIT_MESSAGES"
}

import {
  to = github_repository.landing_page
  id = "perishdev.github.io"
}

resource "github_repository" "landing_page" {
  name        = "perishdev.github.io"
  description = "perish.dev landing page — Jekyll/Cayman, served by GitHub Pages"
  visibility  = "public"
  topics      = ["jekyll", "github-pages", "landing-page"]

  has_issues   = true
  has_projects = false
  has_wiki     = false

  # Same squash-only policy as infra.
  allow_squash_merge     = true
  allow_merge_commit     = false
  allow_rebase_merge     = false
  delete_branch_on_merge = true
}
