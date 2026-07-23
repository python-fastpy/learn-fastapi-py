# Revert Master After Merging a Feature Branch

## Related Files

- [git-merge-types.md](git-merge-types.md) — merge commit vs fast-forward vs squash merge
- [git-cat-file.md](git-cat-file.md) — understanding `git cat-file -p` and git internals
- [git-commit-parents.md](git-commit-parents.md) — all commands to get parent commits, identify master vs feature side
- [git-merge-conflict-resolution.md](git-merge-conflict-resolution.md) — resolving conflicts during `git revert -m 1`

---

# Case 1: Feature Branch Has New Commits (Merge Commit)

## Scenario

You created a feature branch from QA, made new commits (D, E, F),
and merged it into master using `git merge` (merge commit, NOT squash).

## Visual Diagram

```
BEFORE (what happened):

QA branch:        A---B---C
                           \
Feature branch:             D---E---F
                                     \
Master branch:   X---Y---Z-----------M (merge commit, 2 parents)
                          ^           ^
                     you want to     current
                     go back here    state

git log --oneline --graph on master:
*   a1b2c3d Merge branch 'feature' into master
|\
| * f1e2d3c commit F
| * e1d2c3b commit E
| * d1c2b3a commit D
|/
* x9y8z7w commit Z
* y8z7w6v commit Y
```

---

# Case 2: Feature Branch Has NO New Commits (Merge Commit)

## Scenario

You created a feature branch from QA but made NO new commits on it.
The feature branch just points to the same commit as QA (commit C).
Then you merged it into master using `git merge` (merge commit),
which brought all of QA's commits into master.

## Visual Diagram

```
BEFORE (what happened):

QA branch:        A---B---C
                           |
Feature branch:            C  (same commit, no new work)
                           |
Master branch:   X---Y---Z---M (merge commit - brought A, B, C into master)
                          ^   ^
                     want to  current
                     be here  state

git log --oneline --graph on master:
*   a1b2c3d Merge branch 'feature' into master
|\
| * c1b2a3z commit C (from QA)
| * b1a2z3y commit B (from QA)
| * a1z2y3x commit A (from QA)
|/
* x9y8z7w commit Z
```

## Why This Happens

```bash
git checkout qa              # on QA at commit C
git checkout -b feature      # feature now also points to C
# (no new commits made)
git checkout master
git merge feature            # merges QA's history (A, B, C) into master
```

The feature branch acted as a **pointer to QA** — merging it was
effectively the same as merging QA directly into master.

## How to Verify This Case

```bash
# Check if feature branch has any commits that QA doesn't
git log qa..feature --oneline
# If output is EMPTY -> feature has no new commits (this case)
# If output shows commits -> Case 1 above

# Check if both branches point to the same commit
git rev-parse feature
git rev-parse qa
# If both return the same hash -> this case
```

## Key Difference Between Case 1 and Case 2

| Aspect                         | Case 1 (has commits)    | Case 2 (no commits)                         |
|--------------------------------|-------------------------|----------------------------------------------|
| What gets reverted             | Feature's commits D,E,F | QA's commits A,B,C                           |
| Feature branch was             | Actual new work         | Just a pointer to QA                         |
| Surprise factor                | Low (expected)          | High (didn't realize QA came along)          |
| After revert, QA is in master? | Yes (A,B,C stay)        | No (A,B,C are removed)                      |

---

# All Possible Options to Undo the Merge

Both Case 1 and Case 2 use the same options below.
All options assume a **merge commit** (not squash merge).

For other merge types, see [git-merge-types.md](git-merge-types.md).

---

## Option 1: `git revert -m 1` (Safe - Preserves History)

**When to use:** Master is shared with others, or already pushed to remote.

**Why `-m 1`?** A merge commit has 2 parents. `-m 1` means "keep parent 1"
(the master side). See [git-commit-parents.md](git-commit-parents.md) for details.

```
Merge commit M has 2 parents:
  Parent 1 (-m 1) = master side (Z) --> KEEP this one
  Parent 2 (-m 2) = feature side (F) --> discard this one
```

### Steps

```bash
# 1. Switch to master
git checkout master

# 2. Find the merge commit hash
git log --oneline --graph
# *   a1b2c3d (HEAD -> master) Merge branch 'feature' into master  <-- M
# |\
# | * f1e2d3c commit F
# |/
# * x9y8z7w previous commit on master                              <-- Z

# 3. Revert the merge commit
#    -m 1 = keep master side (parent 1), undo feature side
#    Replace a1b2c3d with YOUR actual merge commit hash
git revert -m 1 a1b2c3d

# 4. Push the revert
git push origin master
```

If you get **conflicts**, see [git-merge-conflict-resolution.md](git-merge-conflict-resolution.md).

### Result

```
AFTER:

*   m1r2e3v (HEAD -> master) Revert "Merge branch 'feature' into master"  <-- M'
*   a1b2c3d Merge branch 'feature' into master                            <-- M (still in history)
|\
| * f1e2d3c commit F
|/
* x9y8z7w commit Z

Master: X---Y---Z---M---M'  (M' undoes M's changes, history preserved)
```

### Pros

- History is preserved (M still exists in log)
- No force push needed
- Safe for shared branches
- Other developers are not affected

### Cons

- Adds an extra commit (M')
- If you want to re-merge the same feature branch later, you must
  first revert the revert:

```bash
git revert b2c3d4e    # undo the revert commit M'
git merge feature     # now merge again
```

### What `-m 1` vs `-m 2` Does

```bash
git revert -m 1 a1b2c3d   # undo feature changes, keep master as-is
                            # Result: master goes back to state at Z

git revert -m 2 a1b2c3d   # undo master changes, keep feature as-is
                            # Result: master gets ONLY feature changes (rarely wanted)
```

---

## Option 2: `git reset --hard` (Destructive - Rewrites History)

**When to use:** You are the sole contributor, OR the merge has NOT been pushed yet.

### Steps

```bash
# 1. Switch to master
git checkout master

# 2. Find the commit hash BEFORE the merge (commit Z)
git log --oneline
# a1b2c3d (HEAD -> master) Merge branch 'feature' into master  <-- M
# x9y8z7w previous commit on master                            <-- Z (target)

# 3. Hard reset to the commit before merge
git reset --hard x9y8z7w

# 4. Force push (ONLY if already pushed to remote)
git push --force origin master
```

### Result

```
AFTER:

* x9y8z7w (HEAD -> master) commit Z
* y8z7w6v commit Y

Master: X---Y---Z   (M is completely removed from history)
```

### Pros

- Clean history — merge commit is gone entirely
- Can re-merge the feature branch directly later (no revert-of-revert needed)

### Cons

- Rewrites history (dangerous for shared branches)
- Requires force push if already pushed
- Other developers must resync:
  ```bash
  git fetch origin
  git reset --hard origin/master
  ```

---

## Option 3: `git reset --soft` (Keep Changes Staged)

**When to use:** You want to undo the merge but keep the merged code
changes in your staging area for review or partial re-commit.

### Steps

```bash
# 1. Switch to master
git checkout master

# 2. Soft reset to the commit before merge
git reset --soft x9y8z7w

# 3. Now the merged changes are in staging area
git status   # shows all merged files as staged

# 4. You can:
#    a) Discard everything:
git reset HEAD .
git checkout -- .

#    b) Keep some files and commit:
git reset HEAD file-you-dont-want.py
git commit -m "kept only selected changes from feature merge"

#    c) Review what was merged:
git diff --cached
```

### Result

```
AFTER (before re-committing):

Master: X---Y---Z   (HEAD moved back, but changes are staged)
                 ^
                 HEAD is here, but working directory has merged code
```

### Pros

- Non-destructive to working directory
- Lets you cherry-pick which changes to keep
- Good for partial rollbacks

### Cons

- Requires manual decision on what to keep/discard
- Still rewrites history (needs force push if pushed)

---

## Option 4: `git reset --mixed` (Keep Changes Unstaged)

**When to use:** Similar to soft reset, but you want changes in working
directory (unstaged) instead of staging area.

### Steps

```bash
# 1. Switch to master
git checkout master

# 2. Mixed reset (default behavior of git reset)
git reset x9y8z7w

# 3. Changes are now unstaged in working directory
git status   # shows changes as modified (not staged)

# 4. You can:
#    a) Discard all:
git checkout -- .

#    b) Stage and commit specific files:
git add specific-file.py
git commit -m "kept specific changes"
```

### Result

```
AFTER:

Master: X---Y---Z   (HEAD and index moved back, changes in working dir)
```

### Pros

- Full control over what to keep
- Can review changes file by file before staging

### Cons

- Rewrites history
- More manual work than revert

---

## Option 5: Create a New Branch from Pre-Merge State

**When to use:** You don't want to touch master at all. Instead, create
a new clean branch from before the merge.

### Steps

```bash
# 1. Find the commit before merge
git log master --oneline
# x9y8z7w previous commit on master  <-- Z

# 2. Create a new branch from that commit
git checkout -b master-clean x9y8z7w

# 3. Push the new branch
git push origin master-clean

# 4. Optionally, make this the new master:
#    - In GitHub/GitLab: change default branch to master-clean
#    - Rename branches:
git branch -m master master-broken
git branch -m master-clean master
git push origin master --force
git push origin --delete master-broken
```

### Result

```
AFTER:

master-broken:   X---Y---Z---M   (old master, kept for reference)
master-clean:    X---Y---Z       (new clean branch)
```

### Pros

- Original master is preserved as backup
- No force push needed (until you rename)
- Safest approach — nothing is deleted

### Cons

- More steps involved
- Team needs to switch to new branch
- Confusing if not communicated clearly

---

## Option 6: `git reflog` Recovery (Emergency - After Accidental Reset)

**When to use:** You already did a `git reset --hard` and want to undo
the undo (get the merge back).

### Steps

```bash
# 1. View reflog to find the merge commit
git reflog
# output:
# x9y8z7w HEAD@{0}: reset: moving to x9y8z7w   <-- the reset you did
# a1b2c3d HEAD@{1}: merge feature: Merge ...    <-- the merge commit (M)
# x9y8z7w HEAD@{2}: commit: previous work       <-- Z

# 2. Reset back to the merge commit
#    IMPORTANT: wrap HEAD@{1} in quotes to avoid shell errors
#    PowerShell, Zsh, and some shells treat { } as special characters

# Works in PowerShell, Zsh, Git Bash (safest — always use quotes):
git reset --hard "HEAD@{1}"

# 3. Or just use the actual commit hash directly (always works, no quoting issues):
git reset --hard a1b2c3d
```

### Common Error with HEAD@{1}

```bash
# ERROR: shells interpret { } before git sees them
git reset --hard HEAD@{1}
# PowerShell error: "unexpected token '@{1}'"
# Zsh error:        "no matches found: HEAD@{1}"

# FIX: wrap in double quotes
git reset --hard "HEAD@{1}"

# OR single quotes (works in Bash/Zsh, NOT PowerShell)
git reset --hard 'HEAD@{1}'

# OR just use the commit hash (no quoting needed, always works everywhere)
git reflog                    # find the hash: a1b2c3d
git reset --hard a1b2c3d      # use hash directly
```

### Pros

- Can recover from accidental resets
- Reflog keeps ~90 days of history locally

### Cons

- Only works locally (reflog is not pushed)
- Only available before `git gc` cleans up
- `HEAD@{n}` syntax needs quoting in most shells

---

# Comparison of All Options

| Option                  | History     | Force Push? | Keep Changes? | Re-merge Later?          | Risk    | Needs `-m 1`? |
|-------------------------|-------------|-------------|---------------|--------------------------|---------|---------------|
| 1. `git revert -m 1`   | Preserved   | No          | No            | Need revert-of-revert    | Low     | YES           |
| 2. `git reset --hard`  | Rewritten   | Yes         | No            | Yes, directly            | High    | No            |
| 3. `git reset --soft`  | Rewritten   | Yes         | Yes (staged)  | Yes, directly            | Medium  | No            |
| 4. `git reset --mixed` | Rewritten   | Yes         | Yes (unstaged)| Yes, directly            | Medium  | No            |
| 5. New branch           | Preserved   | No*         | No            | Yes, directly            | Low     | No            |
| 6. Reflog recovery      | Restored    | Maybe       | No            | N/A (recovery)           | Low     | No            |

\* Force push needed only if renaming the new branch to master

---

# Recommendation Decision Tree

```
Do you need to undo a merge on master?
│
├── Was it a MERGE COMMIT or SQUASH MERGE?
│   │                (see git-merge-types.md)
│   ├── MERGE COMMIT (our case) --> use -m 1 with revert
│   └── SQUASH MERGE --> regular revert (no -m flag needed)
│
├── Has the merge been pushed to remote?
│   ├── YES
│   │   ├── Are other people working on master?
│   │   │   ├── YES --> Option 1: git revert -m 1 (safest)
│   │   │   └── NO  --> Option 1 or Option 2 (coordinate force push)
│   │   │
│   │   └── Do you want to keep some of the merged changes?
│   │       └── YES --> Option 3: git reset --soft (review and re-commit)
│   │
│   └── NO (only local)
│       ├── Want clean history? --> Option 2: git reset --hard
│       ├── Want to review changes? --> Option 3 or 4: soft/mixed reset
│       └── Want a safety net? --> Option 5: new branch
│
└── Already did a reset and want to undo it?
    └── Option 6: git reflog recovery
```

---

# Prevention: Check Before Merging

```bash
# See what commits will be merged BEFORE running git merge
git log master..feature --oneline

# See what files will change
git diff master...feature --stat

# Do a dry-run merge (doesn't actually merge)
git merge --no-commit --no-ff feature
git diff --cached --stat    # review
git merge --abort           # cancel

# Check if feature has its own commits or is just a QA pointer
git log qa..feature --oneline
# empty = no new commits (Case 2)
```

---

# Quick Reference Commands

```bash
# See recent commits with graph
git log --oneline --graph --all

# Find merge commits specifically
git log --merges --oneline

# Check if a commit is a merge commit (see git-cat-file.md)
git cat-file -p a1b2c3d | grep parent

# Get parents quickly (see git-commit-parents.md)
git rev-parse a1b2c3d^1    # Parent 1 (master)
git rev-parse a1b2c3d^2    # Parent 2 (feature)

# Check what a revert will do before committing
git revert -m 1 --no-commit a1b2c3d
git diff --cached
git revert --abort

# Verify master is clean after any operation
git status
git log --oneline -5

# Compare two branches
git log branch1..branch2 --oneline

# See reflog for recovery
git reflog --oneline
```

---

# Re-merging After a Revert: Avoiding "Revert the Revert"

## The Problem

After `git revert -m 1`, if you try to merge the same feature branch
again, **Git says "Already up to date"** — it thinks those changes
already exist in history, even though the revert undid them.

```bash
git revert -m 1 a1b2c3d      # undo the merge
git merge feature             # "Already up to date." — nothing happens!
```

## Why This Happens

Git tracks by **commit ancestry**, not by file contents. The feature
commits (D, E, F) are already reachable from master's history
(through the original merge M). The revert only added a new commit
that undid the changes — it didn't remove D, E, F from the graph.

```
Master: X---Y---Z---M---M'(revert)
                    / \
Feature:       D--E--F   (already reachable from M, so Git skips them)
```

## The Standard Fix (Revert the Revert)

```bash
git revert <revert-commit-hash>   # undo the undo
git merge feature                 # now merge again
```

This works but leaves messy history: merge → revert → revert-of-revert → re-merge.

## Alternatives That Avoid the Revert-of-Revert

### Alternative 1: Cherry-pick onto a New Branch

Create a new branch and cherry-pick the original feature commits.
Git sees new commit hashes, so it treats them as fresh changes.

```bash
# 1. Find the original feature commits
git log --oneline feature
# f1e2d3c commit F
# e1d2c3b commit E
# d1c2b3a commit D

# 2. Create a new branch from master
git checkout -b feature-v2 master

# 3. Cherry-pick the feature commits (oldest to newest)
git cherry-pick d1c2b3a e1d2c3b f1e2d3c

# 4. Merge the new branch into master
git checkout master
git merge feature-v2
```

```
RESULT:

Master: X---Y---Z---M---M'(revert)---M2 (merge feature-v2)
                                     /
feature-v2:                    D'--E'--F' (new hashes, same changes)
```

**Pros:** Clean, no revert-of-revert, easy to understand
**Cons:** If feature had many commits, cherry-picking each one is tedious
**Tip:** Use range cherry-pick to avoid listing each commit:

```bash
# Cherry-pick all commits from D to F (D's parent..F)
git cherry-pick d1c2b3a^..f1e2d3c
```

---

### Alternative 2: Rebase Feature Branch (Create New SHAs)

Rebase the feature branch to generate new commit hashes, then merge.
This rewrites the **feature branch** only, not master.

```bash
# 1. Rebase feature branch onto master
#    --no-ff forces new commits even if it could fast-forward
git checkout feature
git rebase --no-ff master

# 2. Now feature has new commit hashes
git log --oneline feature
# a2b3c4d commit F  (new hash, same content)
# b3c4d5e commit E  (new hash)
# c4d5e6f commit D  (new hash)

# 3. Merge into master
git checkout master
git merge feature
```

```
RESULT:

Master: X---Y---Z---M---M'(revert)---M2
                                     /
feature (rebased):             D''--E''--F'' (new hashes)
```

**Pros:** Feature branch stays as one unit, no new branch needed
**Cons:** Rewrites feature branch history — don't do this if others are
working on that feature branch

---

### Alternative 3: Squash Merge the Feature Branch

Squash all feature commits into one new commit. Git sees a brand new
commit with a new hash.

```bash
git checkout master
git merge --squash feature
git commit -m "Re-add feature: D, E, F changes (squashed)"
```

```
RESULT:

Master: X---Y---Z---M---M'(revert)---S (single squashed commit)

S contains all changes from D+E+F combined into one commit
```

**Pros:** Simplest command, one clean commit
**Cons:** Loses individual commit history (D, E, F become one commit S)

---

## Which Alternative to Use?

```
Need to re-merge a feature branch after revert?
│
├── How many commits does the feature have?
│   │
│   ├── Few commits (1-5)
│   │   └── Cherry-pick onto new branch (Alternative 1)
│   │       Simple, clean, preserves individual commits
│   │
│   ├── Many commits (5+)
│   │   ├── Care about individual commit history?
│   │   │   ├── YES --> Rebase the feature branch (Alternative 2)
│   │   │   └── NO  --> Squash merge (Alternative 3)
│   │   │
│   │   └── Others working on the feature branch?
│   │       ├── YES --> Cherry-pick or Squash (don't rebase shared branch)
│   │       └── NO  --> Any alternative works
│   │
│   └── Just want it done, don't care about history?
│       └── Squash merge (Alternative 3) — one command, done
│
└── Or just do the standard revert-of-revert if none of this matters
```

| Alternative              | New Hashes? | Preserves Commits? | Rewrites Feature? | Complexity |
|--------------------------|-------------|---------------------|--------------------|------------|
| Cherry-pick (new branch) | Yes         | Yes                 | No                 | Medium     |
| Rebase feature           | Yes         | Yes                 | Yes                | Low        |
| Squash merge             | Yes         | No (combined)       | No                 | Low        |
| Revert-of-revert         | No          | Yes                 | No                 | Low        |

---

# Lesson Learned

When you create a feature branch from QA without adding commits,
merging that feature branch into master is the same as merging QA.
Always check what you're actually merging:

```bash
# BEFORE merging, always run:
git log master..feature --oneline

# This shows ALL commits that master doesn't have yet
# If you see QA commits here, the merge will bring them too
```
