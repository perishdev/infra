# Secrets

This repo is **public**. Plaintext secrets must never be committed — not in code, not in CI logs, not in `terraform plan` output. A secret that lands in git history is compromised forever; rotation is the only fix.

## Where secrets live

| Secret | Store | Consumed by |
|---|---|---|
| Cloudflare API token | HCP Terraform workspace variable on `cloudflare`, marked sensitive | `terraform` runs in HCP |
| GitHub App ID, installation ID, private key (PEM) | HCP Terraform workspace variables on `github-org`, marked sensitive | `terraform` runs in HCP |
| HCP Terraform user API token | `~/.terraform.d/credentials.tfrc.json` (set by `terraform login`), per maintainer | local Terraform CLI; scripted HCP API calls |

**Nothing encrypted is committed to the repo.** No SOPS, no `git-crypt`. If we ever run our own hosts and need runtime secrets, we pick an out-of-band store then; until that day, all secrets in scope live in HCP workspace variables.

## Why HCP Terraform as the vault

- Workspace variables marked `sensitive` are encrypted at rest and redacted from run logs.
- Runs execute on HCP infrastructure; sensitive values are injected into the run environment, never echoed back to the laptop or to GitHub Actions logs.
- One place to rotate Terraform-time credentials.
- HCP's own state encryption covers everything Terraform writes during a run.

## Cloudflare API token scopes

The token loaded into the `cloudflare` workspace needs **Edit** on every kind of resource we manage. For the current set:

- Zone — DNS — Edit
- Zone — Zone Settings — Edit

If/when we add more resource types, add scope before declaring the resource. For one-shot discovery via [`cf-terraforming`](./import.md), a separate token with **Read** scopes works fine — the user generates it locally, uses it to populate `generated.tf`, then deletes it. The persistent HCP token only needs the scopes that match the resources Terraform actively manages.

## GitHub App setup

The GitHub provider authenticates as a GitHub App, not a PAT. Apps are not tied to a user, support fine-grained permissions, and rotate cleanly.

1. Create the app under the `perishdev` org (Settings → Developer settings → GitHub Apps → New).
2. Permissions: Repository — Administration (read/write), Contents (read), Metadata (read), Pull requests (read/write). Organization — Members (read), Administration (read/write).
3. Install the app on the org, scoped to the repos Terraform manages (currently `perishdev/infra` and `perishdev/perishdev.github.io`).
4. Generate a private key, store the **App ID**, **installation ID**, and **PEM** in the `github-org` HCP workspace as three sensitive variables (`github_app_id`, `github_app_installation_id`, `github_app_pem`).
5. The PEM must include the full `-----BEGIN/END RSA PRIVATE KEY-----` lines. Pasting just the base64 body works for the first request, then breaks on key rotation.

## Rotation

- **Cloudflare token**: rotate yearly or on suspected exposure. Generate the replacement before deleting the old one; update the HCP workspace variable; next run uses the new token.
- **GitHub App private key**: rotate yearly or on suspected exposure. GitHub Apps support multiple active keys — generate the new one, swap the HCP variable, delete the old key.
- **HCP user API token**: rotated when a maintainer leaves. Each maintainer regenerates their own via `terraform login` after revocation.

## Things that look like secrets but aren't

- Cloudflare account ID, zone ID — not secret, but reconnaissance signal. Fine to commit. Both live as `local`s in `terraform/cloudflare/main.tf`.
- GitHub org / repo names, GitHub App ID, installation ID — public anyway. App ID and installation ID are *marked* sensitive in the HCP variables for defense-in-depth, but they're not credentials.
- Resource IDs in Terraform state — state itself lives in HCP, never in the repo.
- The HCP organization name, workspace names — non-secret identifiers.
