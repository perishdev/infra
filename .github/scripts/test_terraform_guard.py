"""Tests for terraform_guard.py. Run: python3 -m unittest discover -s .github/scripts"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

import terraform_guard as guard

REPO = "perishdev/infra"
SHA = "a" * 40


def plan(*changes: tuple[str, list[str]]) -> dict:
    return {
        "format_version": "1.2",
        "resource_changes": [{"address": a, "change": {"actions": acts}} for a, acts in changes],
    }


def pr(**overrides) -> dict:
    base = {
        "merged_at": "2026-10-18T00:00:00Z",
        "merge_commit_sha": SHA,
        "base": {"ref": "main", "repo": {"full_name": REPO}},
        "labels": [{"name": "allow-destroy"}],
    }
    base.update(overrides)
    return base


class DestructiveChanges(unittest.TestCase):
    def test_no_changes(self) -> None:
        self.assertEqual(guard.destructive_changes({"format_version": "1.2"}), [])

    def test_create_update_read_noop_forget_are_not_destructive(self) -> None:
        p = plan(("a.b", ["create"]), ("a.c", ["update"]), ("a.d", ["read"]), ("a.e", ["no-op"]), ("a.f", ["forget"]))
        self.assertEqual(guard.destructive_changes(p), [])

    def test_delete_and_both_replacement_orders(self) -> None:
        p = plan(("a.del", ["delete"]), ("a.cbd", ["create", "delete"]), ("a.dbc", ["delete", "create"]))
        self.assertEqual([c["address"] for c in guard.destructive_changes(p)], ["a.del", "a.cbd", "a.dbc"])

    def test_unknown_action_fails_closed(self) -> None:
        with self.assertRaises(guard.GuardError):
            guard.destructive_changes(plan(("a.b", ["obliterate"])))

    def test_empty_actions_fail_closed(self) -> None:
        with self.assertRaises(guard.GuardError):
            guard.destructive_changes(plan(("a.b", [])))

    def test_unsupported_format_fails_closed(self) -> None:
        for bad in [None, [], {"format_version": "2.0"}, {"format_version": "1.2", "resource_changes": {}}]:
            with self.subTest(bad=bad), self.assertRaises(guard.GuardError):
                guard.destructive_changes(bad)


class Warning(unittest.TestCase):
    def test_empty_when_nothing_destructive(self) -> None:
        self.assertEqual(guard.warning([]), "")

    def test_labels_replace_and_delete(self) -> None:
        text = guard.warning([{"address": "a.x", "actions": ["delete"]}, {"address": "a.y", "actions": ["delete", "create"]}])
        self.assertIn("- ` a.x `: delete", text)
        self.assertIn("- ` a.y `: replace", text)
        self.assertIn("allow-destroy", text)

    def test_backticks_in_address_are_fenced(self) -> None:
        self.assertIn("`` a[\"`k`\"] ``", guard.warning([{"address": 'a["`k`"]', "actions": ["delete"]}]))

    def test_truncates_to_limit(self) -> None:
        changes = [{"address": f"a.r{i}", "actions": ["delete"]} for i in range(1000)]
        text = guard.warning(changes, 2000, "https://run")
        self.assertLessEqual(len(text), 2000)
        self.assertIn("list truncated", text)


class CommentBody(unittest.TestCase):
    def test_stays_under_github_limit(self) -> None:
        body = guard.comment_body(
            marker="<!-- terraform-plan:github -->", leaf="github", status="changes", sha=SHA,
            run_url="https://run", plan="x" * 200_000, changes=[],
        )
        self.assertLessEqual(len(body), guard.COMMENT_LIMIT)
        self.assertTrue(body.startswith("<!-- terraform-plan:github -->\n"))
        self.assertIn("truncated", body)

    def test_destructive_notice_comes_before_plan(self) -> None:
        body = guard.comment_body(
            marker="<!-- m -->", leaf="github", status="changes", sha=SHA, run_url="https://run",
            plan="PLAN", changes=[{"address": "a.x", "actions": ["delete"]}],
        )
        self.assertLess(body.index("Deletes / replacements"), body.index("PLAN"))


class OptedIn(unittest.TestCase):
    def test_merged_labelled_pr_for_this_commit(self) -> None:
        self.assertTrue(guard.opted_in([pr()], SHA, REPO))

    def test_repository_match_is_case_insensitive(self) -> None:
        self.assertTrue(guard.opted_in([pr()], SHA, "PerishDev/Infra"))

    def test_refusals(self) -> None:
        cases = {
            "no PRs (direct push)": [],
            "not merged": [pr(merged_at=None)],
            "different commit": [pr(merge_commit_sha="b" * 40)],
            "not into main": [pr(base={"ref": "dev", "repo": {"full_name": REPO}})],
            "other repository": [pr(base={"ref": "main", "repo": {"full_name": "someone/fork"}})],
            "label missing": [pr(labels=[{"name": "safe-to-plan"}])],
        }
        for name, pulls in cases.items():
            with self.subTest(name):
                self.assertFalse(guard.opted_in(pulls, SHA, REPO))


class Cli(unittest.TestCase):
    def run_inspect(self, raw: bytes) -> tuple[int, str, str]:
        stdin = io.TextIOWrapper(io.BytesIO(raw))
        out, err = io.StringIO(), io.StringIO()
        original = guard.sys.stdin
        guard.sys.stdin = stdin
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = guard.main(["inspect"])
        finally:
            guard.sys.stdin = original
        return code, out.getvalue(), err.getvalue()

    def test_inspect_prints_only_addresses_and_actions(self) -> None:
        p = plan(("a.x", ["delete"]))
        p["resource_changes"][0]["change"]["before"] = {"secret": "hunter2"}
        code, out, _ = self.run_inspect(json.dumps(p).encode())
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), [{"address": "a.x", "actions": ["delete"]}])
        self.assertNotIn("hunter2", out)

    def test_inspect_error_does_not_echo_input(self) -> None:
        code, out, err = self.run_inspect(b'{"secret": "hunter2", broken')
        self.assertEqual(code, 1)
        self.assertNotIn("hunter2", out + err)


if __name__ == "__main__":
    unittest.main()
