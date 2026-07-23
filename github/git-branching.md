# Git Branching

---

## What is a Branch?

A branch is just a pointer to a commit. Creating a branch is instant —
it doesn't copy files, it just creates a new pointer.

```
main:      A---B---C         <-- main points here
                    \
feature:             D---E   <-- feature points here

HEAD = which branch you're currently on
```

---

## Create a Branch

```bash
# Create a new branch (stays on current branch)
git branch feature

# Create AND switch to a new branch
git checkout -b feature

# Modern way (git 2.23+) — create and switch
git switch -c feature

# Create branch from a specific commit
git checkout -b feature a1b2c3d

# Create branch from another branch
git checkout -b feature develop
```

### What Happens Internally

```bash
git checkout -b feature
# 1. Creates file: .git/refs/heads/feature
# 2. That file contains the commit hash that feature points to
# 3. Updates HEAD to point to feature

cat .git/refs/heads/feature
# output: a1b2c3d4e5f6...  (commit hash)

cat .git/HEAD
# output: ref: refs/heads/feature   (currently on feature branch)
```

---

## Switch Branches

```bash
# Old way
git checkout main

# Modern way (git 2.23+)
git switch main

# Switch to previous branch (like cd -)
git checkout -
git switch -
```

### When Switching Fails

```bash
# ERROR: you have uncommitted changes that would conflict
git switch main
# error: Your local changes to 'file.py' would be overwritten by checkout

# Fix options:
git stash               # stash changes, switch, then pop later
git commit -m "wip"     # commit work-in-progress
git checkout -- file.py # discard changes (CAREFUL: loses work)
```

---

## List Branches

```bash
# List local branches (* = current branch)
git branch
# * feature
#   main
#   develop

# List remote branches
git branch -r
#   origin/main
#   origin/develop
#   origin/feature

# List ALL branches (local + remote)
git branch -a
# * feature
#   main
#   origin/main
#   origin/develop

# List branches with last commit info
git branch -v
# * feature  a1b2c3d add login page
#   main     x9y8z7w initial commit

# List branches with tracking info
git branch -vv
# * feature  a1b2c3d [origin/feature] add login page
#   main     x9y8z7w [origin/main] initial commit

# List branches that contain a specific commit
git branch --contains a1b2c3d

# List branches merged into current branch
git branch --merged

# List branches NOT merged into current branch
git branch --no-merged
```

---

## Delete a Branch

```bash
# Delete a fully merged branch (safe)
git branch -d feature
# Deleted branch feature (was a1b2c3d)

# Force delete an unmerged branch (CAREFUL: loses commits)
git branch -D feature

# Delete a remote branch
git push origin --delete feature
# or
git push origin :feature

# Clean up stale remote tracking branches
# (remote branch deleted, but local still shows it)
git fetch --prune
# or
git remote prune origin
```

### When Delete Fails

```bash
git branch -d feature
# error: The branch 'feature' is not fully merged.

# This means feature has commits not in the current branch
# Verify what would be lost:
git log main..feature --oneline

# If you're sure, force delete:
git branch -D feature
```

---

## Rename a Branch

```bash
# Rename current branch
git branch -m new-name

# Rename any branch
git branch -m old-name new-name

# Rename on remote (delete old + push new)
git push origin --delete old-name
git push origin new-name
git push origin -u new-name    # set upstream
```

---

## Tracking Branches (Local vs Remote)

```bash
# See which local branches track which remote branches
git branch -vv

# Set upstream (tracking) for current branch
git branch -u origin/feature
# or when pushing for the first time
git push -u origin feature

# Create a local branch that tracks a remote branch
git checkout --track origin/feature
# or
git checkout feature    # auto-tracks if only one remote has it

# Remove upstream tracking
git branch --unset-upstream
```

### How Tracking Works

```
Local branch:  feature  -->  tracks  -->  origin/feature (remote)

git status will then show:
  "Your branch is ahead of 'origin/feature' by 2 commits"
  "Your branch is behind 'origin/feature' by 3 commits"
  "Your branch and 'origin/feature' have diverged"
```

---

## Comparing Branches

```bash
# Commits in feature that are NOT in main
git log main..feature --oneline

# Commits in main that are NOT in feature
git log feature..main --oneline

# All commits in either but not both
git log main...feature --oneline

# Files changed between branches
git diff main..feature --stat

# Actual code diff between branches
git diff main..feature
```

---

## Common Branching Workflows

### Feature Branch Workflow

```
main:       A---B---C-----------M
                     \         /
feature:              D---E---F

1. git checkout -b feature main     # create feature from main
2. (make commits D, E, F)
3. git checkout main                # switch to main
4. git merge feature                # merge feature into main
5. git branch -d feature            # delete feature branch
```

### Git Flow

```
main:       A-----------M1----------M2
             \         /           /
develop:      B---C---D---E---F---G
                   \     /
feature:            X---Y
```

### Trunk-Based Development

```
main:    A---B---C---D---E---F---G
              \   /       \   /
short-lived:   X           Y

(very short-lived feature branches, merged quickly)
```

---

## Quick Reference

```bash
# Create and switch
git checkout -b feature       # or: git switch -c feature

# List
git branch                    # local
git branch -a                 # all
git branch -vv                # with tracking info

# Delete
git branch -d feature         # safe (merged only)
git branch -D feature         # force
git push origin --delete feat # remote

# Rename
git branch -m new-name

# Compare
git log main..feature --oneline
git diff main..feature --stat

# Track remote
git push -u origin feature
git branch -vv
```

---

## Related

- [git-stash.md](git-stash.md) — save work when switching branches
- [git-rebase.md](git-rebase.md) — rebase vs merge for integrating branches
- [git-merge-types.md](git-merge-types.md) — what happens when you merge
