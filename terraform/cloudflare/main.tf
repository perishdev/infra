# Cloudflare resources.
#
# Single workspace because we manage a single apex domain in a single
# Cloudflare account. Environment separation (e.g. staging.<domain> vs
# <domain>, app-staging Worker vs app Worker) lives at the resource level
# inside this workspace, typically via for_each over an "environments" map.
#
# Split into per-env workspaces only if we later add a second apex domain
# dedicated to staging, or move staging into a separate Cloudflare account.
