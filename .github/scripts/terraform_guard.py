#!/usr/bin/env python3
"""Refuse Terraform deletes and replacements unless the merged PR opted in.

"Destructive apply opt-in" in .infra-copilot/decisions.md. Three subcommands, all
stdlib-only so they run on a bare GitHub runner:

  inspect   plan JSON on stdin -> JSON list of {address, actions} that delete
  comment   build the PR plan comment, deletes/replacements listed first
  enforce   in an apply job: fail unless the PR that produced GITHUB_SHA
            carries the `allow-destroy` label

Only addresses and action names ever leave this process. Plan JSON can hold
secret values, so it is never written to disk, logged, or echoed in errors.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

LABEL = "allow-destroy"
KNOWN_ACTIONS = {"no-op", "create", "read", "update", "delete", "forget"}
MAX_PLAN_BYTES = 128 * 1024 * 1024
COMMENT_LIMIT = 65000  # GitHub rejects comment bodies over 65536 characters.
SUMMARY_LIMIT = 900_000  # GitHub silently drops step summaries over 1 MiB.

Change = dict[str, Any]


class GuardError(Exception):
    """A failure whose message is safe to print: it never quotes plan content."""


def destructive_changes(plan: Any) -> list[Change]:
    """Return every resource change whose actions include `delete`.

    That covers plain destroys and both replacement orders. `forget` (from a
    `removed { lifecycle { destroy = false } }` block) is not a delete.
    Anything unrecognised fails closed rather than being waved through.
    """
    if not isinstance(plan, dict) or not str(plan.get("format_version", "")).startswith("1."):
        raise GuardError("Cannot inspect destructive actions: invalid or unsupported Terraform plan JSON.")
    resources = plan.get("resource_changes", [])
    if not isinstance(resources, list):
        raise GuardError("Cannot inspect destructive actions: invalid or unsupported Terraform plan JSON.")
    changes: list[Change] = []
    for resource in resources:
        address = resource.get("address") if isinstance(resource, dict) else None
        change = resource.get("change") if isinstance(resource, dict) else None
        actions = change.get("actions") if isinstance(change, dict) else None
        if (
            not isinstance(address, str)
            or not isinstance(actions, list)
            or not actions
            or not all(action in KNOWN_ACTIONS for action in actions)
        ):
            raise GuardError("Cannot inspect destructive actions: invalid resource change.")
        if "delete" in actions:
            changes.append({"address": address, "actions": actions})
    return changes


def _code_span(value: str) -> str:
    longest = 0
    run = 0
    for char in value:
        run = run + 1 if char == "`" else 0
        longest = max(longest, run)
    fence = "`" * (longest + 1)
    return f"{fence} {value} {fence}"


def warning(changes: list[Change], max_length: int | None = None, run_url: str = "") -> str:
    """Markdown listing of deletes and replacements, or "" when there are none."""
    if not changes:
        return ""
    heading = f"### Deletes / replacements ({len(changes)})\n\n"
    footer = (
        f"\n\nApply is blocked unless the merged PR carries `{LABEL}`. "
        "This label records intent, not authorization.\n\n"
    )
    omitted = f"\n…list truncated; [complete destructive inventory in the run summary]({run_url})."
    listing = ""
    for change in changes:
        kind = "replace" if "create" in change["actions"] else "delete"
        line = f"- {_code_span(change['address'])}: {kind}\n"
        if max_length is not None and len(heading + listing + line + footer + omitted) > max_length:
            return heading + listing + omitted + footer
        listing += line
    return heading + listing + footer


def summary_warning(changes: list[Change]) -> str:
    notice = warning(changes)
    if len(notice.encode()) > SUMMARY_LIMIT:
        raise GuardError(
            "Destructive inventory exceeds the step-summary limit; split the destructive change into smaller PRs."
        )
    return notice


def comment_body(
    *, marker: str, leaf: str, status: str, sha: str, run_url: str, plan: str, changes: list[Change]
) -> str:
    notice = warning(changes, 12000, run_url)

    def frame(text: str) -> str:
        return (
            f"{marker}\n{notice}### `terraform/{leaf}` plan: {status}\n\n"
            f"Commit {sha[:7]} · [run]({run_url})\n\n"
            f"<details><summary>Plan</summary>\n\n````\n{text}\n````\n</details>"
        )

    prefix = "…(truncated, full plan in the run summary)\n"
    budget = COMMENT_LIMIT - len(frame(""))
    if len(plan) > budget:
        plan = prefix + plan[-(budget - len(prefix)) :]
    return frame(plan)


def opted_in(pulls: list[dict[str, Any]], sha: str, repository: str) -> bool:
    """True only if the merged PR that produced exactly `sha` into main carries LABEL.

    An open PR, an older merged PR, or a direct push never qualifies.
    """
    for pr in pulls:
        if (
            pr.get("merged_at")
            and pr.get("merge_commit_sha") == sha
            and pr.get("base", {}).get("ref") == "main"
            and str(pr.get("base", {}).get("repo", {}).get("full_name", "")).lower() == repository.lower()
            and any(label.get("name") == LABEL for label in pr.get("labels", []))
        ):
            return True
    return False


def _load_json(raw: bytes) -> Any:
    if len(raw) > MAX_PLAN_BYTES:
        raise GuardError("Unable to inspect Terraform plan JSON (128 MiB limit).")
    try:
        return json.loads(raw)
    except ValueError:
        # The decode error quotes the input, which may hold secrets.
        raise GuardError("Unable to inspect Terraform plan JSON (128 MiB limit).") from None


def _saved_plan(leaf: str) -> Any:
    try:
        raw = subprocess.run(
            ["terraform", "show", "-json", "tfplan"],
            cwd=f"terraform/{leaf}",
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        # CalledProcessError carries stdout/stderr; never let it reach the log.
        raise GuardError("Unable to read saved Terraform plan JSON; refusing apply.") from None
    return _load_json(raw)


def _pulls_for_commit(repository: str, sha: str) -> list[dict[str, Any]]:
    try:
        out = subprocess.run(
            ["gh", "api", "--paginate", "--slurp", f"repos/{repository}/commits/{sha}/pulls"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        pages = json.loads(out)
    except (OSError, subprocess.CalledProcessError, ValueError):
        raise GuardError("Could not list the PRs for this commit; refusing deletes/replacements.") from None
    return [pr for page in pages for pr in page]


def _append_summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path and text:
        with open(path, "a", encoding="utf-8") as summary:
            summary.write(text)


def enforce(leaf: str) -> None:
    changes = destructive_changes(_saved_plan(leaf))
    if not changes:
        return
    _append_summary(summary_warning(changes))
    repository = os.environ["GITHUB_REPOSITORY"]
    sha = os.environ["GITHUB_SHA"]
    if not opted_in(_pulls_for_commit(repository, sha), sha, repository):
        raise GuardError(
            f"Refusing deletes/replacements: the PR that produced this commit must carry {LABEL}. "
            "Direct pushes cannot opt in."
        )
    print(f"Deletes/replacements explicitly opted into by the merged PR ({LABEL}).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect", help="plan JSON on stdin -> destructive changes JSON on stdout")
    comment = sub.add_parser("comment", help="print the PR plan comment body")
    comment.add_argument("--leaf", required=True)
    comment.add_argument("--status", required=True)
    comment.add_argument("--sha", required=True)
    comment.add_argument("--run-url", required=True)
    comment.add_argument("--plan-file", required=True)
    comment.add_argument("--changes-file", help="output of `inspect`; omit when the plan failed")
    enforce_cmd = sub.add_parser("enforce", help="fail unless deletes were opted into")
    enforce_cmd.add_argument("--leaf", required=True)
    args = parser.parse_args(argv)

    try:
        if args.command == "inspect":
            print(json.dumps(destructive_changes(_load_json(sys.stdin.buffer.read()))))
        elif args.command == "comment":
            with open(args.plan_file, encoding="utf-8") as plan_file:
                plan = plan_file.read()
            changes: list[Change] = []
            if args.changes_file:
                with open(args.changes_file, encoding="utf-8") as changes_file:
                    changes = json.load(changes_file)
            _append_summary(summary_warning(changes))
            print(
                comment_body(
                    marker=f"<!-- terraform-plan:{args.leaf} -->",
                    leaf=args.leaf,
                    status=args.status,
                    sha=args.sha,
                    run_url=args.run_url,
                    plan=plan,
                    changes=changes,
                )
            )
        else:
            enforce(args.leaf)
    except GuardError as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
