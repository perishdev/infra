# Secrets

This repo is **public**. Plaintext secrets must never be committed — not in code, not in CI logs, not in `terraform plan` output. A secret that lands in git history is compromised forever; rotation is the only fix.

## Where secrets live

| Secret | Store | Consumed by |
|---|---|---|
| Cloudflare API token | HCP Terraform workspace variable (sensitive) | `terraform` runs |
| GitHub App ID, installation ID, private key | HCP Terraform workspace variable (sensitive) | `terraform` runs |
| HCP Terraform API token | GitHub Actions encrypted secret (`TF_API_TOKEN`) | CI workflow, to trigger HCP runs |

**Nothing encrypted is committed to the repo.** No SOPS, no `git-crypt`. If we ever run our own hosts and need runtime secrets, we pick an out-of-band store then; until that day, all secrets in scope live in HCP workspace variables.

## Why HCP Terraform as the vault

- Workspace variables marked `sensitive` are encrypted at rest and redacted from run logs.
- A leaked CI token can trigger a plan but can't read the underlying secret values — they're injected into the run environment, not exposed to the workflow.
- One place to rotate Terraform-time credentials.

## GitHub App setup

The GitHub provider authenticates as a GitHub App, not a PAT. Apps are not tied to a user, support fine-grained permissions, and rotate cleanly.

1. Create the app under the `perishdev` org (Settings → Developer settings → GitHub Apps → New).
2. Permissions: only what Terraform needs to manage (start narrow — repos, teams, secrets — expand on demand).
3. Install the app on the org, scoped to the repos Terraform will touch.
4. Generate a private key, store the App ID, installation ID, and PEM in the HCP Terraform workspace as three sensitive variables.
5. Configure the [`integrations/github`](https://registry.terraform.io/providers/integrations/github/latest/docs#github-app-installation) provider with those three values.

## Rotation

- **Cloudflare token**: rotate yearly or on any suspected exposure. Generate the replacement before deleting the old one; update the HCP workspace variable; next run uses the new token.
- **GitHub App private key**: rotate yearly or on any suspected exposure. GitHub Apps support multiple active keys — generate a new one, swap the workspace variable, delete the old key.
- **HCP Terraform API token**: rotate when any maintainer with access leaves; update the GH Actions secret.

## Things that look like secrets but aren't

- Cloudflare account ID, zone IDs — not secret, but reconnaissance signal. Fine to commit.
- GitHub org name, repo names — public anyway.
- Resource IDs in Terraform state — state itself lives in HCP, never in the repo.
