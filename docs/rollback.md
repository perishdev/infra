# Rollback

What to do when an apply made things worse. Pick the lowest-cost option that fixes the problem.

## 1. Revert the merged PR (preferred)

If the last apply was driven by a merged PR and the previous state was fine, the cleanest fix is to revert.

```sh
gh pr view <bad-pr> --repo perishdev/infra --json mergeCommit --jq '.mergeCommit.oid'
# create a branch, revert the merge commit
git fetch origin
git checkout -b revert/<bad-pr> origin/main
git revert -m 1 <merge-sha>
git push -u origin revert/<bad-pr>
gh pr create --base main --title "revert: ..." --body "Reverts #<bad-pr> because ..."
```

This re-runs the workspaces touched by the original PR. HCP plan should be the mirror of what the original PR applied. Confirm and apply.

Use when: the bad change was code-driven, the previous state is what you want back, and the revert generates a plan you'd be comfortable applying.

## 2. Discard the unconfirmed run (no apply yet)

If a PR merged and HCP planned but you haven't confirmed apply, the plan is sitting at "needs confirmation." Just discard it.

```sh
HCP_TOKEN=$(jq -r '.credentials["app.terraform.io"].token' ~/.terraform.d/credentials.tfrc.json)
curl -s -X POST "https://app.terraform.io/api/v2/runs/<run-id>/actions/discard" \
  -H "Authorization: Bearer $HCP_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{"comment":"discarding — see <revert-pr>"}'
```

Or click **Discard Run** in the HCP UI. State stays at the previous apply.

Then open a revert PR per option 1.

Use when: the plan looks wrong on review but the apply hasn't run yet.

## 3. Cancel an in-progress apply

If you catch a bad apply mid-flight, cancel it. HCP stops at the current resource boundary — partially applied state is possible.

```sh
curl -s -X POST "https://app.terraform.io/api/v2/runs/<run-id>/actions/cancel" \
  -H "Authorization: Bearer $HCP_TOKEN"
```

Then run a fresh plan to see what survived; you may need state surgery (option 4) or a revert (option 1).

Use when: apply is currently running and you realised it shouldn't.

## 4. State surgery (`terraform state rm` + re-import)

When Terraform's understanding of a resource doesn't match reality (drift it can't reconcile), the fix is to remove the resource from state and re-import.

```sh
cd terraform/<leaf>
terraform state rm <resource-address>
# fix the code or import block
terraform plan      # should show import action
```

The re-import must come from a properly-shaped `import` block in code, not the legacy `terraform import` CLI. Open a PR for it.

Use when: a resource exists in cloud but Terraform's state for it is wrong; or vice versa.

## 5. Emergency: admin override of branch protection

For situations where a fix has to land *now* and the required checks won't pass (e.g. HCP itself is down so the `Terraform Cloud/...` check can never green). The protection rule has `enforce_admins = false`, so org admins can merge anyway.

GitHub UI: PR page → "Merge without waiting for requirements to be met (bypass branch protections)". Confirm.

After: open a docs PR (or this rollback playbook) recording exactly why the bypass was used. The bypass leaves an audit trail in the repo's protection logs.

Use when: there's a real fire and the gates can't be opened normally.

## 6. Worst case: rebuild from cf-terraforming

If state is corrupted beyond surgery, the nuclear option is to throw away the workspace, recreate it, and re-import everything via `cf-terraforming` (Cloudflare) or by hand (GitHub).

1. In HCP UI → workspace → Settings → Delete. Confirm.
2. Recreate the workspace per [`setup.md`](./setup.md) step 2.
3. Reload sensitive variables.
4. Run [`cf-terraforming`](./import.md) against the live Cloudflare state.
5. Build new `import` blocks for everything, plan, apply.

This is multi-hour work and is a real outage for any apply-gated change in flight. Avoid unless options 1–5 are all impossible.

Use when: HCP state is genuinely lost or so wrong that surgery is harder than rebuild.

## Things that AREN'T rollback

- **Reverting a Cloudflare dashboard change** — Cloudflare doesn't have a "previous version" button for most resources. If someone clicked something destructive in the dashboard, Terraform plan will show the drift, but reconstructing the previous state means knowing what it was. Keep `terraform plan` output from clean PRs as a reference.
- **Reverting an HCP workspace settings change** — same story. HCP doesn't version workspace settings. If a setting was changed in the UI, the fix is to set it back in the UI.

`★ Insight` (Markdown-as-callout): the most common real-world rollback is option 1 (revert + new apply). Options 2–6 are increasingly rare. If your gut says "I need option 4 or 5," double-check the diff is actually as bad as you think — state surgery can introduce drift you didn't intend.
