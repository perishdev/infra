# Vendor limits

What free tiers cover, where the cliffs are, and how close we are. Updated by hand; numbers age — verify against vendor docs before making a decision based on these.

## HCP Terraform — Free tier

| Resource | Free tier | We're at |
|---|---|---|
| Managed resources | **500** | ~15 |
| Active users | **3** | 1 |
| Self-service workspaces | unlimited | 2 |
| Concurrent runs | 1 | enough |
| Run minutes | not metered on Free | n/a |
| API rate limit | 30 req/sec authenticated | well under |

**Cliff to watch:** the 500-resource limit. Once over, **Standard tier** charges $0.00014 per resource-hour above 500 — roughly $0.10/resource/month. At our current scale (15 resources), we have ~33× headroom. At 100 resources, still no charge. At 600, ~$10/month.

**When we'd cross 500:** unlikely without a deliberate change in scope (e.g. managing many small Cloudflare zone settings as individual resources, or onboarding a large set of GitHub repos). Worth re-checking before bulk-importing anything.

**Doc:** <https://www.hashicorp.com/products/terraform/pricing>

## Cloudflare — Free plan

| Resource | Free plan | Notes |
|---|---|---|
| Zones | 1 per account | we're at 1 (`perish.dev`) |
| DNS records | unmetered | we're at ~11 |
| Email Routing rules | unmetered (but limits on destinations) | a few |
| Workers requests | 100k/day | not using |
| R2 storage | 10 GB | not using |
| Pages projects | unlimited | not using (we use GitHub Pages) |
| Page Rules (legacy) | 3 | 0 active |
| Redirect Rules (Rulesets) | 10 | 0 |
| API rate limit | **1200 req / 5 min** | matters for big imports |

**Cliff to watch:** the API rate limit during bulk operations (cf-terraforming on a huge account, or a Terraform plan that touches many resources). For our current scale, irrelevant.

**Doc:** <https://developers.cloudflare.com/fundamentals/api/reference/limits/>

## GitHub — Free plan (for personal accounts and orgs)

| Resource | Free plan | Notes |
|---|---|---|
| Public repos | unlimited | we're at 2 |
| Private repos | unlimited | we're at 0 |
| GitHub Actions minutes | 2000/month (private repos only; public repos are free) | not metered for us |
| Storage for packages/Actions | 500 MB | unused |
| GitHub Pages bandwidth | **100 GB/month soft limit** | landing page — way under |
| GitHub Pages builds | 10/hour | a few during bootstrap |
| API rate limit (token) | **5000/hour** authenticated | well under |
| API rate limit (anon) | 60/hour | unused |
| Branch protection | available on public repos free | enabled |
| Required reviewers | available | not used (solo) |

**Cliff to watch:** GitHub Pages 100 GB/month bandwidth if `perish.dev` ever gets viral. Currently a static landing page; well under.

**Doc:** <https://docs.github.com/en/get-started/learning-about-github/githubs-plans>

## Let's Encrypt (via GitHub Pages)

| Resource | Limit | Notes |
|---|---|---|
| Certificates per registered domain per week | 50 | n/a — we get 1 |
| Failed validations per hour | 5 | bit us during the cert-wedge debug |
| Renewals | automatic, GitHub handles | every ~60 days for a 90-day cert |

**Cliff to watch:** during cert-provisioning debugging (the toggle dance), do NOT loop on failed setups — Let's Encrypt rate-limits failures and locks you out for an hour. Wait between attempts.

**Doc:** <https://letsencrypt.org/docs/rate-limits/>

## What we'd pay if every meter ran red

Pessimistic upper bound at this repo's *current* shape:

| Vendor | Free → first-paid threshold | Estimated cost at 2× current usage |
|---|---|---|
| HCP Terraform | 500 resources | $0 |
| Cloudflare | sustained traffic on Pro features | $0 (we're not on Pro) |
| GitHub | 100 GB Pages bandwidth | $0 |
| Let's Encrypt | always free | $0 |

Total: **$0/month** at current usage; no realistic path to a bill until the scope of what's managed grows substantially.

## Monitoring (deliberately absent)

We don't have alerting on any of these thresholds because none is close. If/when we approach a cliff, add a `docs/monitoring.md` for whatever check triggers it. For now: re-read this doc once a year, or whenever scope changes meaningfully.
