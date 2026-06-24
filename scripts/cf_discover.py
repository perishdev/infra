#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Discover existing Cloudflare resources for the zone managed in this repo and
emit Terraform `import` blocks + resource stubs so they can be brought under
Terraform management without recreation.

Run:
    CF_API_TOKEN=... uv run scripts/cf_discover.py

Output is written to terraform/cloudflare/generated.tf. Review the diff,
adjust resource names if needed, then commit.

The token needs read scopes on every kind of resource being discovered:
- Zone.DNS:Read
- Account.Workers Scripts:Read
- Zone.Workers Routes:Read
- Account.Workers R2 Storage:Read
- Account.Pages:Read
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

API_BASE = "https://api.cloudflare.com/client/v4"

# Identifiers — must match terraform/cloudflare/main.tf locals. Kept here so
# this script is self-contained and runnable without parsing HCL.
ACCOUNT_ID = "d8a72309e747515805b614574ea7f323"
ZONE_ID = "78ff9bdc9f1a38c01a935d3d079b1e7b"
DOMAIN = "perish.dev"

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "terraform" / "cloudflare" / "generated.tf"


@dataclass
class Emitted:
    """One Terraform block pair: an `import` and its matching `resource`."""

    import_block: str
    resource_block: str


def _request(path: str, token: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    url = f"{API_BASE}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Cloudflare API {e.code} on {path}: {body}") from None


def _paginated(path: str, token: str, page_size: int = 100) -> Iterator[dict[str, Any]]:
    page = 1
    while True:
        data = _request(path, token, {"page": str(page), "per_page": str(page_size)})
        result = data.get("result") or []
        yield from result
        info = data.get("result_info") or {}
        if page >= int(info.get("total_pages") or 1):
            return
        page += 1


def _sanitize(name: str) -> str:
    """Map an arbitrary name to a valid Terraform identifier (snake-ish)."""
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", name).strip("_").lower()
    if not s or not s[0].isalpha():
        s = f"_{s}"
    return s


def _unique(names: Iterator[str]) -> Iterator[str]:
    seen: dict[str, int] = {}
    for n in names:
        if n not in seen:
            seen[n] = 0
            yield n
        else:
            seen[n] += 1
            yield f"{n}_{seen[n]}"


def discover_dns(token: str) -> list[Emitted]:
    records = list(_paginated(f"/zones/{ZONE_ID}/dns_records", token))
    raw_names = [
        _sanitize(f"{r['type'].lower()}_{r['name'].replace(DOMAIN, '').strip('.') or 'apex'}")
        for r in records
    ]
    uniq = list(_unique(iter(raw_names)))
    out: list[Emitted] = []
    for tf_name, r in zip(uniq, records):
        addr = f"cloudflare_dns_record.{tf_name}"
        import_block = f'import {{\n  to = {addr}\n  id = "{ZONE_ID}/{r["id"]}"\n}}\n'
        body_lines = [
            "  zone_id = local.zone_id",
            f'  name    = "{r["name"]}"',
            f'  type    = "{r["type"]}"',
            f"  content = {json.dumps(r.get('content', ''))}",
            f"  ttl     = {r.get('ttl', 1)}",
        ]
        if r.get("proxied") is not None and r["type"] in {"A", "AAAA", "CNAME"}:
            body_lines.append(f"  proxied = {str(r['proxied']).lower()}")
        if r.get("priority") is not None:
            body_lines.append(f"  priority = {r['priority']}")
        resource_block = (
            f'resource "cloudflare_dns_record" "{tf_name}" {{\n'
            + "\n".join(body_lines)
            + "\n}\n"
        )
        out.append(Emitted(import_block, resource_block))
    return out


def discover_workers_scripts(token: str) -> list[Emitted]:
    scripts = _request(f"/accounts/{ACCOUNT_ID}/workers/scripts", token).get("result") or []
    out: list[Emitted] = []
    for s in scripts:
        name = s["id"]
        tf_name = _sanitize(name)
        addr = f"cloudflare_workers_script.{tf_name}"
        out.append(
            Emitted(
                import_block=f'import {{\n  to = {addr}\n  id = "{ACCOUNT_ID}/{name}"\n}}\n',
                resource_block=(
                    f'resource "cloudflare_workers_script" "{tf_name}" {{\n'
                    f"  account_id  = local.account_id\n"
                    f'  script_name = "{name}"\n'
                    f"  # content = file(\"./workers/{name}.js\")  # populate from prod\n"
                    f"}}\n"
                ),
            )
        )
    return out


def discover_workers_routes(token: str) -> list[Emitted]:
    routes = _request(f"/zones/{ZONE_ID}/workers/routes", token).get("result") or []
    out: list[Emitted] = []
    for i, r in enumerate(routes):
        tf_name = _sanitize(r.get("pattern", f"route_{i}"))
        addr = f"cloudflare_workers_route.{tf_name}"
        body_lines = [
            "  zone_id = local.zone_id",
            f'  pattern = "{r["pattern"]}"',
        ]
        if r.get("script"):
            body_lines.append(f'  script  = "{r["script"]}"')
        out.append(
            Emitted(
                import_block=f'import {{\n  to = {addr}\n  id = "{ZONE_ID}/{r["id"]}"\n}}\n',
                resource_block=(
                    f'resource "cloudflare_workers_route" "{tf_name}" {{\n'
                    + "\n".join(body_lines)
                    + "\n}\n"
                ),
            )
        )
    return out


def discover_r2_buckets(token: str) -> list[Emitted]:
    data = _request(f"/accounts/{ACCOUNT_ID}/r2/buckets", token).get("result") or {}
    buckets = data.get("buckets") if isinstance(data, dict) else data
    out: list[Emitted] = []
    for b in buckets or []:
        name = b["name"]
        tf_name = _sanitize(name)
        addr = f"cloudflare_r2_bucket.{tf_name}"
        out.append(
            Emitted(
                import_block=f'import {{\n  to = {addr}\n  id = "{ACCOUNT_ID}/default/{name}"\n}}\n',
                resource_block=(
                    f'resource "cloudflare_r2_bucket" "{tf_name}" {{\n'
                    f"  account_id = local.account_id\n"
                    f'  name       = "{name}"\n'
                    f"}}\n"
                ),
            )
        )
    return out


def discover_pages_projects(token: str) -> list[Emitted]:
    projects = _request(f"/accounts/{ACCOUNT_ID}/pages/projects", token).get("result") or []
    out: list[Emitted] = []
    for p in projects:
        name = p["name"]
        tf_name = _sanitize(name)
        addr = f"cloudflare_pages_project.{tf_name}"
        out.append(
            Emitted(
                import_block=f'import {{\n  to = {addr}\n  id = "{ACCOUNT_ID}/{name}"\n}}\n',
                resource_block=(
                    f'resource "cloudflare_pages_project" "{tf_name}" {{\n'
                    f"  account_id = local.account_id\n"
                    f'  name       = "{name}"\n'
                    f"  # production_branch and build_config not introspected — fill in manually\n"
                    f"}}\n"
                ),
            )
        )
    return out


def main() -> int:
    token = os.environ.get("CF_API_TOKEN")
    if not token:
        print("error: CF_API_TOKEN not set", file=sys.stderr)
        return 1

    sections: list[tuple[str, list[Emitted]]] = [
        ("DNS records", discover_dns(token)),
        ("Workers scripts", discover_workers_scripts(token)),
        ("Workers routes", discover_workers_routes(token)),
        ("R2 buckets", discover_r2_buckets(token)),
        ("Pages projects", discover_pages_projects(token)),
    ]

    chunks: list[str] = [
        "# Generated by scripts/cf_discover.py — do not edit by hand.\n"
        "# Re-run the script to refresh; review the diff before committing.\n"
    ]
    for title, items in sections:
        chunks.append(f"\n# ─── {title} ({len(items)}) " + "─" * (50 - len(title)) + "\n")
        if not items:
            chunks.append(f"# (none)\n")
            continue
        for e in items:
            chunks.append("\n" + e.import_block + "\n" + e.resource_block)

    OUTPUT_PATH.write_text("".join(chunks))
    total = sum(len(items) for _, items in sections)
    print(f"wrote {OUTPUT_PATH.relative_to(Path.cwd())} — {total} resources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
