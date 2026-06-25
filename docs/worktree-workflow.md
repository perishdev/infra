# Worktree workflow

Optional but recommended for any maintainer doing more than one branch of work at a time.

## What `git worktree` does

A normal `git clone` gives you one checkout — one directory, one branch at a time. Switching branches means stashing or committing work-in-progress, then `git checkout`. Painful when you have a long-running branch and need to peek at `main`.

`git worktree` lets a single repository have **multiple checked-out branches in different directories**, all sharing the same `.git` (objects, refs, hooks). Switching branches becomes `cd ../other-worktree`.

## How this repo is laid out (one convention)

```
~/.superset/projects/infra                           main      (the primary worktree)
~/.superset/worktrees/infra/feat/<topic>             feat/...  (one per active branch)
~/.superset/worktrees/infra/chore/<topic>            chore/...
~/.superset/worktrees/infra/docs/<topic>             docs/...
```

The session you're reading was done in `~/.superset/worktrees/infra/feat/useful-gull/`. The primary worktree at `~/.superset/projects/infra` stayed on `main`, useful as a "what does main look like right now?" reference.

This layout is a convention, not enforced by anything. Use whatever directory shape fits.

## Quick reference

```sh
# Create a worktree on a new branch off main
git fetch origin
git worktree add -b feat/<topic> ~/.superset/worktrees/infra/feat/<topic> origin/main

# Switch into it
cd ~/.superset/worktrees/infra/feat/<topic>

# Normal git workflow from here

# When the branch is merged and the worktree is no longer useful
git worktree remove ~/.superset/worktrees/infra/feat/<topic>
# (or if files were changed: `--force`)

# List all worktrees attached to this repo
git worktree list

# Prune stale worktree refs after manual rm of a worktree dir
git worktree prune
```

## When the convention earns its keep

- **Two unrelated changes at the same time** — you can flip between them by `cd`-ing, no stash dance.
- **Reviewing a PR locally while your branch is dirty** — `git worktree add /tmp/review origin/<their-branch>`, do the review, `git worktree remove /tmp/review`.
- **Running tests on `main` while developing on a branch** — primary worktree on `main`, secondary on `feat/...`, both can have a `terraform plan` going.

## When it doesn't

- For a one-shot small PR, the cognitive cost of `cd`-ing isn't worth the worktree setup. Just branch in your normal checkout.
- If you don't use multiple branches concurrently, worktrees add nothing.

## Caveats

- Each worktree has its own working directory but they share git objects. A `git fetch` in one updates refs for all. That's the feature.
- You can't have two worktrees on the same branch — git enforces this so you can't accidentally commit conflicting changes to the same ref from two places.
- Some IDEs and tools assume "one working dir per project." If your editor or LSP gets confused, the workaround is usually opening each worktree as a separate project window.
- `gitignored` files in `.terraform/`, `node_modules/`, etc. are per-worktree, not shared. Each worktree's tooling state is independent.

## When this doc earns its keep

If a contributor doesn't already know `git worktree`, they don't need to learn it to contribute — a plain clone is fine. This doc exists for the contributor who's juggling two branches and wishing the dance were easier.
