# Email Routing for perish.dev.
#
# Forwards incoming mail at any address on perish.dev to a verified
# destination. The MX/SPF/DKIM/DMARC records that make this work live in
# dns.tf; this file manages the forwarding *behaviour* itself.
#
# Today: one verified destination (hasansezertasan@gmail.com) and a single
# catch-all rule. Add per-pattern `cloudflare_email_routing_rule` resources
# below if/when specific addresses (hello@, security@, etc.) need to route
# to different destinations.

# ── Destination addresses ──────────────────────────────────────────
#
# Cloudflare sends a verification email on first create. Once verified, the
# verification timestamp persists; if this resource is destroyed and
# recreated, the destination must be re-verified by clicking a fresh link.

import {
  to = cloudflare_email_routing_address.primary
  id = "${local.account_id}/83420559539a4b41904202a81f6fde37"
}

resource "cloudflare_email_routing_address" "primary" {
  account_id = local.account_id
  email      = "hasansezertasan@gmail.com"
}

# ── Catch-all rule ─────────────────────────────────────────────────
#
# One per zone; forwards anything that doesn't match a more specific rule.

import {
  to = cloudflare_email_routing_catch_all.this
  id = local.zone_id
}

resource "cloudflare_email_routing_catch_all" "this" {
  zone_id = local.zone_id
  enabled = true
  name    = ""

  matchers = [
    {
      type = "all"
    },
  ]

  actions = [
    {
      type  = "forward"
      value = ["hasansezertasan@gmail.com"]
    },
  ]
}
