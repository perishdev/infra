# DNS records for perish.dev.
#
# Email records were imported from existing Cloudflare state via
# `cf-terraforming` (see docs/import.md). Resource labels were renamed
# for readability — the `id` values inside `import` blocks remain the
# canonical Cloudflare record IDs.
#
# Apex (perish.dev) and www are served by GitHub Pages from the repo
# perishdev/perishdev.github.io. Proxied is false so GitHub can issue
# its Let's Encrypt cert for the custom domain — once the cert is live
# the proxy can optionally be re-enabled with SSL mode = Full.

# ── Email routing (Cloudflare-managed) ─────────────────────────────

import {
  to = cloudflare_dns_record.mx_route1
  id = "${local.zone_id}/20010945014f7700d4e7c7a5866d2049"
}

resource "cloudflare_dns_record" "mx_route1" {
  zone_id  = local.zone_id
  type     = "MX"
  name     = local.domain
  content  = "route1.mx.cloudflare.net"
  priority = 86
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}

import {
  to = cloudflare_dns_record.mx_route2
  id = "${local.zone_id}/9bdbcd39cd11cfa3e24b0edb97a3662c"
}

resource "cloudflare_dns_record" "mx_route2" {
  zone_id  = local.zone_id
  type     = "MX"
  name     = local.domain
  content  = "route2.mx.cloudflare.net"
  priority = 42
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}

import {
  to = cloudflare_dns_record.mx_route3
  id = "${local.zone_id}/9ec5860b93cbcdd1f5ede53edf1b0ae8"
}

resource "cloudflare_dns_record" "mx_route3" {
  zone_id  = local.zone_id
  type     = "MX"
  name     = local.domain
  content  = "route3.mx.cloudflare.net"
  priority = 65
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}

# ── Email authentication ───────────────────────────────────────────

import {
  to = cloudflare_dns_record.spf
  id = "${local.zone_id}/5274d7018143bd6008bc5a02ab22498e"
}

resource "cloudflare_dns_record" "spf" {
  zone_id  = local.zone_id
  type     = "TXT"
  name     = local.domain
  content  = "\"v=spf1 include:_spf.mx.cloudflare.net ~all\""
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}

import {
  to = cloudflare_dns_record.dmarc
  id = "${local.zone_id}/d61861f4a14141533d1233be20d6de94"
}

resource "cloudflare_dns_record" "dmarc" {
  zone_id  = local.zone_id
  type     = "TXT"
  name     = "_dmarc.${local.domain}"
  content  = "\"v=DMARC1; p=none; rua=mailto:9532460379b24a828af6ac1ceb60bd15@dmarc-reports.cloudflare.net\""
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}

import {
  to = cloudflare_dns_record.dkim_cf2024_1
  id = "${local.zone_id}/729abab2c08608f8b2d143891c4941fb"
}

resource "cloudflare_dns_record" "dkim_cf2024_1" {
  zone_id  = local.zone_id
  type     = "TXT"
  name     = "cf2024-1._domainkey.${local.domain}"
  content  = "\"v=DKIM1; h=sha256; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAiweykoi+o48IOGuP7GR3X0MOExCUDY/BCRHoWBnh3rChl7WhdyCxW3jgq1daEjPPqoi7sJvdg5hEQVsgVRQP4DcnQDVjGMbASQtrY4WmB1VebF+RPJB2ECPsEDTpeiI5ZyUAwJaVX7r6bznU67g7LvFq35yIo4sdlmtZGV+i0H4cpYH9+3JJ78k\" \"m4KXwaf9xUJCWF6nxeD+qG6Fyruw1Qlbds2r85U9dkNDVAS3gioCvELryh1TxKGiVTkg4wqHTyHfWsp7KD3WQHYJn0RyfJJu6YEmL77zonn7p2SRMvTMP3ZEXibnC9gz3nnhR6wcYL8Q7zXypKTMD58bTixDSJwIDAQAB\""
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}

# ── Apex + www, served by GitHub Pages ─────────────────────────────
#
# GitHub Pages' four documented anycast IPs for apex domains:
#   https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site#configuring-an-apex-domain

resource "cloudflare_dns_record" "apex_gh_pages_1" {
  zone_id  = local.zone_id
  type     = "A"
  name     = local.domain
  content  = "185.199.108.153"
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}

resource "cloudflare_dns_record" "apex_gh_pages_2" {
  zone_id  = local.zone_id
  type     = "A"
  name     = local.domain
  content  = "185.199.109.153"
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}

resource "cloudflare_dns_record" "apex_gh_pages_3" {
  zone_id  = local.zone_id
  type     = "A"
  name     = local.domain
  content  = "185.199.110.153"
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}

resource "cloudflare_dns_record" "apex_gh_pages_4" {
  zone_id  = local.zone_id
  type     = "A"
  name     = local.domain
  content  = "185.199.111.153"
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}

resource "cloudflare_dns_record" "www_cname" {
  zone_id  = local.zone_id
  type     = "CNAME"
  name     = "www.${local.domain}"
  content  = "perishdev.github.io"
  proxied  = false
  tags     = []
  ttl      = 1
  settings = {}
}
