# Git Submodules

Git submodules let you include one Git repository inside another while keeping their histories separate. The parent repo tracks a specific commit of the child repo rather than copying its files.

## When Do You Need Submodules?

- **Shared libraries or dependencies** that live in their own repo and are used across multiple projects.
- **Third-party projects** you want to pin to a known-good commit (e.g., Moonshot data and UI repos in this project).
- **Monorepo-style composition** where independently versioned components are assembled into a larger project.
- **Vendor code** you want to track upstream changes for without forking.

Without submodules, dropping a `.git`-containing directory into your repo creates an "embedded repository" — clones of the parent won't contain the embedded repo's files and won't know how to fetch them.

## How It Works

When you add a submodule, Git does two things:

1. Creates a `.gitmodules` file at the repo root that maps the submodule path to its remote URL.
2. Records the exact commit SHA the submodule should point to in the parent's tree.

The submodule directory itself is not stored as regular files in the parent — it's a pointer to a commit in another repo.

## Adding a Submodule

```bash
git submodule add <remote-url> <path>
```

Example from this project:

```bash
git submodule add https://github.com/aiverify-foundation/moonshot-data.git moonshot-data
git submodule add https://github.com/aiverify-foundation/moonshot-ui.git moonshot-ui
```

This stages `.gitmodules` and the submodule entries. Commit them:

```bash
git commit -m "feat: add moonshot submodules"
```

## Cloning a Repo That Has Submodules

A regular `git clone` will create the submodule directories but leave them empty. You have two options:

**Option A — Clone with submodules in one step:**

```bash
git clone --recurse-submodules <repo-url>
```

**Option B — Initialize after cloning:**

```bash
git clone <repo-url>
cd <repo>
git submodule init
git submodule update
```

Or combined:

```bash
git submodule update --init
```

For nested submodules (submodules within submodules):

```bash
git submodule update --init --recursive
```

## Updating a Submodule to Latest Upstream

By default, a submodule is pinned to the commit recorded in the parent. To pull the latest changes:

```bash
# Enter the submodule directory
cd moonshot-data

# Fetch and checkout the latest from the desired branch
git fetch origin
git checkout origin/main

# Go back to the parent repo
cd ..

# Stage and commit the updated submodule pointer
git add moonshot-data
git commit -m "chore: update moonshot-data to latest"
```

Or update all submodules at once:

```bash
git submodule update --remote
git add .
git commit -m "chore: update all submodules to latest"
```

## Checking Submodule Status

```bash
# Show which commit each submodule points to
git submodule status

# Show submodule summary (commits ahead/behind)
git submodule summary
```

## Removing a Submodule

There is no single `git submodule rm` command. Follow these steps:

```bash
# 1. Remove the submodule entry from .gitmodules
git config -f .gitmodules --remove-section submodule.<path>

# 2. Remove the submodule entry from .git/config
git config --remove-section submodule.<path>

# 3. Unstage and remove the submodule directory
git rm --cached <path>
rm -rf <path>

# 4. Remove the submodule's metadata
rm -rf .git/modules/<path>

# 5. Commit
git commit -m "chore: remove <path> submodule"
```

## Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| Empty submodule directories after clone | Submodules aren't fetched by default | Run `git submodule update --init --recursive` |
| `modified: moonshot-data (new commits)` | You pulled new commits inside the submodule but didn't commit the pointer in the parent | `git add moonshot-data && git commit` |
| `modified: moonshot-data (dirty)` | Uncommitted changes inside the submodule directory | `cd moonshot-data` and commit or discard changes there |
| Detached HEAD inside submodule | Submodules check out a specific commit, not a branch | `cd moonshot-data && git checkout main` before making changes |
| Adding a repo directory without `submodule add` | Creates an embedded repo that clones can't fetch | Remove with `git rm --cached <path>` and re-add with `git submodule add` |

## Submodules in This Project

This repo uses submodules for the AI Verify Foundation's Project Moonshot:

| Submodule | Purpose | Remote |
|-----------|---------|--------|
| `moonshot-data` | LLM evaluation test assets (datasets, metrics, attack modules, prompt templates) | `https://github.com/aiverify-foundation/moonshot-data.git` |
| `moonshot-ui` | Next.js UI for running benchmarks and red-teaming sessions | `https://github.com/aiverify-foundation/moonshot-ui.git` |

After cloning this repo, run:

```bash
git submodule update --init
```

This fetches both Moonshot repositories at the pinned commits.
