# Revert Master After Merging a Feature Branch

## Related Files

- [git-merge-types.md](git-merge-types.md) — merge commit vs fast-forward vs squash merge
- [git-cat-file.md](git-cat-file.md) — understanding `git cat-file -p` and git internals
- [git-commit-parents.md](git-commit-parents.md) — all commands to get parent commits, identify master vs feature side
- [git-merge-conflict-resolution.md](git-merge-conflict-resolution.md) — resolving conflicts during `git revert -m 1`

---

---

________________________________________________________________________________

# Case 1: Feature Branch Has New Commits (Merge Commit)

## Scenario

You created a feature branch from QA, made new commits (D, E, F),
and merged it into master using `git merge` (merge commit, NOT squash).

## Visual Diagram

```
QA branch:        A---B---C
                           \
Feature branch:             D---E---F
                                     \
Master branch:   X---Y---Z-----------M (merge commit, 2 parents)
                          ^           ^
                     you want to     current
                     go back here    state
```

```
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

---

________________________________________________________________________________

# Case 2: Feature Branch Has NO New Commits (Merge Commit)

## Scenario

You created a feature branch from QA but made NO new commits on it.
The feature branch just points to the same commit as QA (commit C).
Then you merged it into master using `git merge` (merge commit),
which brought all of QA's commits into master.

## Visual Diagram

```
QA branch:        A---B---C
                           |
Feature branch:            C  (same commit, no new work)
                           |
Master branch:   X---Y---Z---M (merge commit - brought A, B, C into master)
                          ^   ^
                     want to  current
                     be here  state
```

```
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

---

________________________________________________________________________________

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
git checkout master
git log --oneline --graph                # find the merge commit hash
git revert -m 1 a1b2c3d                  # revert the merge commit
git push origin master
```

If you get **conflicts**, see [git-merge-conflict-resolution.md](git-merge-conflict-resolution.md).

### Result

```
AFTER:

Master: X---Y---Z---M---M'  (M' undoes M's changes, history preserved)

*   m1r2e3v Revert "Merge branch 'feature' into master"  <-- M'
*   a1b2c3d Merge branch 'feature' into master            <-- M (still in history)
|\
| * f1e2d3c commit F
|/
* x9y8z7w commit Z
```

### Pros and Cons

| Pros                              | Cons                                          |
|-----------------------------------|-----------------------------------------------|
| History preserved (M still in log)| Adds an extra commit (M')                     |
| No force push needed              | Re-merging same branch needs revert-of-revert |
| Safe for shared branches          |                                                |
| Other developers not affected     |                                                |

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
git checkout master
git log --oneline                        # find commit hash BEFORE the merge (Z)
git reset --hard x9y8z7w                 # hard reset to before merge
git push --force origin master           # ONLY if already pushed to remote
```

### Result

```
AFTER:

Master: X---Y---Z   (M is completely removed from history)

* x9y8z7w (HEAD -> master) commit Z
* y8z7w6v commit Y
```

### Pros and Cons

| Pros                                   | Cons                                          |
|----------------------------------------|-----------------------------------------------|
| Clean history — merge commit gone      | Rewrites history (dangerous for shared branches)|
| Can re-merge directly later            | Requires force push if already pushed         |
|                                        | Other devs must resync: `git reset --hard origin/master` |

---

## Option 3: `git reset --soft` (Keep Changes Staged)

**When to use:** You want to undo the merge but keep the merged code
changes in your staging area for review or partial re-commit.

### Steps

```bash
git checkout master
git reset --soft x9y8z7w                 # soft reset to before merge
git status                                # shows all merged files as staged
```

After the reset you can:

```bash
# a) Discard everything:
git reset HEAD .
git checkout -- .

# b) Keep some files and commit:
git reset HEAD file-you-dont-want.py
git commit -m "kept only selected changes from feature merge"

# c) Review what was merged:
git diff --cached
```

### Pros and Cons

| Pros                                | Cons                                         |
|-------------------------------------|----------------------------------------------|
| Non-destructive to working dir      | Requires manual decision on what to keep     |
| Cherry-pick which changes to keep   | Still rewrites history (needs force push)    |
| Good for partial rollbacks          |                                              |

---

## Option 4: `git reset --mixed` (Keep Changes Unstaged)

**When to use:** Similar to soft reset, but you want changes in working
directory (unstaged) instead of staging area.

### Steps

```bash
git checkout master
git reset x9y8z7w                        # mixed reset (default)
git status                                # shows changes as modified (not staged)
```

After the reset you can:

```bash
# a) Discard all:
git checkout -- .

# b) Stage and commit specific files:
git add specific-file.py
git commit -m "kept specific changes"
```

### Pros and Cons

| Pros                            | Cons                         |
|---------------------------------|------------------------------|
| Full control over what to keep  | Rewrites history             |
| Review changes file by file     | More manual work than revert |

---

## Option 5: Create a New Branch from Pre-Merge State

**When to use:** You don't want to touch master at all. Instead, create
a new clean branch from before the merge.

### Steps

```bash
git log master --oneline                  # find commit before merge (Z)
git checkout -b master-clean x9y8z7w      # create clean branch
git push origin master-clean
```

Optionally, make this the new master:

```bash
git branch -m master master-broken
git branch -m master-clean master
git push origin master --force
git push origin --delete master-broken
```

### Result

```
master-broken:   X---Y---Z---M   (old master, kept for reference)
master-clean:    X---Y---Z       (new clean branch)
```

### Pros and Cons

| Pros                               | Cons                                     |
|------------------------------------|------------------------------------------|
| Original master preserved as backup| More steps involved                      |
| No force push needed (until rename)| Team needs to switch to new branch       |
| Safest approach                    | Confusing if not communicated clearly    |

---

## Option 6: `git reflog` Recovery (Emergency - After Accidental Reset)

**When to use:** You already did a `git reset --hard` and want to undo
the undo (get the merge back).

### Steps

```bash
git reflog
# x9y8z7w HEAD@{0}: reset: moving to x9y8z7w   <-- the reset you did
# a1b2c3d HEAD@{1}: merge feature: Merge ...    <-- the merge commit (M)

# Use quotes to avoid shell errors with { }
git reset --hard "HEAD@{1}"

# Or just use the commit hash directly (always works):
git reset --hard a1b2c3d
```

### Common Shell Error with HEAD@{1}

```bash
# ERROR: shells interpret { } as special characters
git reset --hard HEAD@{1}                 # FAILS in PowerShell and Zsh

# FIX options:
git reset --hard "HEAD@{1}"              # double quotes (works everywhere)
git reset --hard 'HEAD@{1}'              # single quotes (Bash/Zsh only, NOT PowerShell)
git reset --hard a1b2c3d                  # use hash directly (always works)
```

### Pros and Cons

| Pros                                | Cons                                     |
|-------------------------------------|------------------------------------------|
| Recovers from accidental resets     | Only works locally (reflog not pushed)   |
| Reflog keeps ~90 days of history    | Only available before `git gc` cleans up |

---

---

________________________________________________________________________________

# When Master Is Protected (Cannot Push Directly)

In most teams, master has branch protection rules — no direct pushes allowed.
You must create a revert on a separate branch and raise a PR.

## Why You Can't Just "Merge to Fix It"

Merging **ADDS** commits — it doesn't remove them. There's no merge
operation that subtracts changes. You need `git revert`, which creates
a NEW commit that applies the inverse diff of the merge.

## Why "Reset on a Branch" Doesn't Work Either

```
You might think: "I'll create a branch, reset it to before the merge,
and PR that into master."

undo-branch:  X---Y---Z          (reset to Z — BEHIND master)
master:       X---Y---Z---M      (has M — AHEAD)

PR: undo-branch → master = "Already up to date"
```

The branch has NO new commits that master doesn't already have.
Z is already in master's history. The branch is **BEHIND**, not ahead.

A PR can only merge **NEW** commits into master.
It cannot move master's pointer backward — that's what `git reset` does,
but you can't reset a protected branch.

The only way to "subtract" through a PR is to **ADD** a new commit
that contains the **INVERSE** of the changes — that's `git revert`.

## Steps (PR-Based Revert Workflow)

```bash
git checkout master
git pull origin master
git log --oneline --merges -5             # find the merge commit hash

git checkout -b revert-feature-merge      # create revert branch
git revert -m 1 a1b2c3d                   # revert the merge commit
git push origin revert-feature-merge      # push the revert branch
# Create PR: revert-feature-merge → master
```

## What the PR Diff Shows

```
The PR removes exactly what the feature merge added:
  - Files added by feature     → deleted
  - Lines added by feature     → removed
  - Lines deleted by feature   → restored
  - Files modified by feature  → reverted to pre-merge state
```

## Result

```
BEFORE:
master (protected):  X---Y---Z---M

AFTER PR merged:
master:              X---Y---Z---M---M' (clean, no force push)
```

The revert branch is a **throwaway** — delete it after the PR merges.

---

---

________________________________________________________________________________

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

---

________________________________________________________________________________

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
│   │   ├── Is master protected?
│   │   │   └── YES --> PR-based revert (see "When Master Is Protected")
│   │   │
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

---

________________________________________________________________________________

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

---

________________________________________________________________________________

# Quick Reference Commands

```bash
git log --oneline --graph --all          # recent commits with graph
git log --merges --oneline               # find merge commits
git cat-file -p a1b2c3d | grep parent   # check if merge commit
git rev-parse a1b2c3d^1                  # parent 1 (master side)
git rev-parse a1b2c3d^2                  # parent 2 (feature side)
git log branch1..branch2 --oneline       # compare two branches
git reflog --oneline                     # see reflog for recovery
```

Dry-run a revert before committing:

```bash
git revert -m 1 --no-commit a1b2c3d
git diff --cached                        # review what changes
git revert --abort                       # cancel if not happy
```

---

---

________________________________________________________________________________

# Re-merging After a Revert

## The Problem

After `git revert -m 1`, if you try to merge the same feature branch
again, **Git says "Already up to date"** — nothing happens.

```bash
git revert -m 1 a1b2c3d      # undo the merge
git merge feature             # "Already up to date." — FAILS
```

## Why This Happens

Git tracks by **commit ancestry**, not by file contents. The feature
commits (D, E, F) are still reachable from master's history through
the original merge M. The revert only added a new commit that undid
the changes — it didn't remove D, E, F from the graph.

```
Master: X---Y---Z---M---M'(revert)
                    /
Feature:       D--E--F   (still reachable from M, so Git skips them)
```

---

## Fix 1: Revert the Revert (Standard Fix)

### Current State

```
* r1e2v3t Revert "Merge branch 'feature' into master"  <-- M' (revert)
*   a1b2c3d Merge branch 'feature' into master          <-- M
|\
| * f1e2d3c commit F
| * e1d2c3b commit E
| * d1c2b3a commit D
|/
* x9y8z7w commit Z

Code state: feature changes are GONE from the files
Git graph:  feature commits D, E, F are still REACHABLE through M
```

### Steps

```bash
git log --oneline -5                     # find the revert commit hash (M')
git revert r1e2v3t                       # revert the revert — no -m flag needed
git push origin master
```

### Why No `-m` Flag This Time?

The revert commit M' is a **regular commit** (1 parent), not a merge commit.

| Commit | Type           | Parents      | Needs -m? |
|--------|----------------|--------------|-----------|
| M      | Merge commit   | Z and F      | YES       |
| M'     | Regular commit | M            | NO        |

Rule: `-m` is ONLY for merge commits (2+ parents).

### Result

```
* q1w2e3r Revert "Revert "Merge ..."   <-- M'' (feature code is BACK)
* r1e2v3t Revert "Merge ..."           <-- M'  (removed feature code)
*   a1b2c3d Merge branch 'feature'      <-- M   (added feature code)
|\
| * f1e2d3c commit F
| * e1d2c3b commit E
| * d1c2b3a commit D
|/
* x9y8z7w commit Z

History: merge → revert → revert-of-revert (messy but safe)
```

### If Master Is Protected

Same pattern — branch + PR:

```bash
git checkout master && git pull origin master
git checkout -b revert-the-revert
git revert r1e2v3t
git push origin revert-the-revert
# Create PR: revert-the-revert → master
```

### With NEW Commits on the Feature Branch

If you added new commits G, H to feature after the original merge + revert:

```bash
# Step 1: Revert the revert (brings back D, E, F)
git revert r1e2v3t

# Step 2: Merge feature again (picks up only G, H)
git merge feature
```

```
* m2e3r4g Merge branch 'feature'        <-- M2 (brings G, H)
|\
| * h1g2f3e commit H (new)
| * g1f2e3d commit G (new)
* | q1w2e3r Revert "Revert ..."         <-- M'' (D,E,F restored)
* | r1e2v3t Revert "Merge ..."          <-- M'
* | a1b2c3d Merge branch 'feature'      <-- M
```

---

## Fix 2: Cherry-pick onto a New Branch

Create a new branch and cherry-pick the original feature commits.
Git sees new commit hashes, so it treats them as fresh changes.

```bash
git log --oneline feature                # find original commits
git checkout -b feature-v2 master        # new branch from master
git cherry-pick d1c2b3a e1d2c3b f1e2d3c  # cherry-pick (oldest to newest)
git checkout master
git merge feature-v2
```

Range shortcut (avoids listing each commit):

```bash
git cherry-pick d1c2b3a^..f1e2d3c
```

```
RESULT:

Master: X---Y---Z---M---M'(revert)---M2
                                     /
feature-v2:                    D'--E'--F' (new hashes, same changes)
```

| Pros                              | Cons                               |
|-----------------------------------|------------------------------------|
| Clean, no revert-of-revert        | Tedious if many commits            |
| Preserves individual commits      | Need to create a new branch        |

---

## Fix 3: Rebase Feature Branch (Create New SHAs)

Rebase the feature branch to generate new commit hashes, then merge.
Rewrites the **feature branch** only, not master.

```bash
git checkout feature
git rebase --no-ff master                # new hashes for D, E, F
git checkout master
git merge feature
```

| Pros                              | Cons                                          |
|-----------------------------------|-----------------------------------------------|
| Feature branch stays as one unit  | Rewrites feature branch history               |
| No new branch needed              | Don't use if others share the feature branch  |

---

## Fix 4: Squash Merge the Re-merge

Squash all feature commits into one new commit with a new hash.

```bash
git checkout master
git merge --squash feature
git commit -m "Re-add feature: D, E, F changes (squashed)"
```

| Pros                  | Cons                                        |
|-----------------------|---------------------------------------------|
| Simplest command      | Loses individual commit history (D,E,F → S) |
| One clean commit      |                                             |

---

## Which Fix to Use?

```
Need to re-merge a feature branch after revert?
│
├── Few commits (1-5)
│   └── Cherry-pick onto new branch (Fix 2)
│
├── Many commits (5+)
│   ├── Care about individual commit history?
│   │   ├── YES --> Rebase the feature branch (Fix 3)
│   │   └── NO  --> Squash merge (Fix 4)
│   │
│   └── Others working on the feature branch?
│       ├── YES --> Cherry-pick or Squash (don't rebase shared branch)
│       └── NO  --> Any fix works
│
├── Just want it done?
│   └── Squash merge (Fix 4) — one command, done
│
└── None of this matters?
    └── Revert the revert (Fix 1)
```

| Fix                        | New Hashes? | Preserves Commits? | Rewrites Feature? |
|----------------------------|-------------|---------------------|--------------------|
| 1. Revert-of-revert        | No          | Yes                 | No                 |
| 2. Cherry-pick (new branch)| Yes         | Yes                 | No                 |
| 3. Rebase feature          | Yes         | Yes                 | Yes                |
| 4. Squash merge            | Yes         | No (combined)       | No                 |

---

---

________________________________________________________________________________

# How to Avoid the Revert-Revert Problem Entirely

The revert-revert problem exists ONLY because of **merge commits**.

## Why Merge Commits Cause This

A merge commit links feature commits (D, E, F) into master's
ancestry graph. Even after reverting, Git still "sees" them.

```
MERGE COMMIT:

Feature:  D---E---F
                   \
Master:   X---Y---Z---M          M links D, E, F into master's graph

After revert:  git merge feature  →  "Already up to date" (FAILS)
```

## Squash Merge Avoids It

A squash commit creates a brand-new commit with no link to D, E, F.

```
SQUASH MERGE:

Feature:  D---E---F              D, E, F are NOT in master's graph

Master:   X---Y---Z---S          S is independent (new hash)

After revert:  git merge feature  →  WORKS (D, E, F are "new" to Git)
```

## Side-by-Side

```bash
# MERGE COMMIT workflow (has the problem)
git merge feature                # creates M with 2 parents
git revert -m 1 <M-hash>        # needs -m flag
git merge feature                # "Already up to date" — FAILS

# SQUASH MERGE workflow (no problem)
git merge --squash feature       # stages changes
git commit -m "Add feature"      # creates S with 1 parent
git revert <S-hash>              # no -m flag needed
git merge feature                # WORKS directly
```

## Tradeoff

| Squash merge pros                     | Squash merge cons                         |
|---------------------------------------|-------------------------------------------|
| Simpler revert (no -m, no revert-revert) | Loses individual commit history on master |
| Cleaner master history                | Feature branch shows as "unmerged" in Git |
| Re-merge just works                   | Many teams mandate merge commits          |

## If You Cannot Use Squash Merge

Your options to re-merge after revert:

| Approach                          | Notes                                          |
|-----------------------------------|-------------------------------------------------|
| Revert the revert (Fix 1)        | Messy history but zero risk                    |
| Cherry-pick onto new branch (Fix 2)| Best balance — new hashes, preserves commits |
| Rebase the feature branch (Fix 3)| Only if no one else shares the branch          |
| Squash only the re-merge (Fix 4) | Use squash just for the recovery step          |

---

---

________________________________________________________________________________

# Real-World Fix Strategy (From Experience)

## Step 1: Visualize the Problem First

Before doing anything, open a Git client that shows the commit tree
(GitKraken, SourceTree, Fork, or `git log --oneline --graph --all`).

Visualizing helps identify the problem. Example: a developer reverted
a cherry-picked commit in QA that was originally pushed to develop —
this caused conflicts between develop and QA on every future merge
because Git replays the revert.

## Step 2: Choose Your Fix

### Option A: Resolve Conflicts Manually

Go through each conflict carefully. Understand WHAT was reverted and WHY.
Decide for each file: keep the reverted state or restore the original.

**Warning:** Requires extreme accuracy. A wrong resolution silently drops changes.

### Option B: Reset the Branch and Re-merge from Scratch

When the branch is too tangled to resolve conflicts safely,
start over by resetting the branch to before the mess began.

**Steps:**

```bash
# 1. Ask developers to stop pushing to the affected branch

# 2. Temporarily allow force push on the protected branch
#    GitHub: Settings → Branches → Branch protection rules

# 3. Find the last clean commit (before the bad revert/merge)
git log --oneline --graph

# 4. Reset the branch to the clean state
git checkout qa
git reset --hard <clean-commit>

# 5. Re-merge the branches that should be in there
git merge develop
# resolve conflicts fresh — without the revert pollution

# 6. Force push
git push --force origin qa

# 7. IMMEDIATELY restore branch protection
```

### What `git reset --hard` Does Here

```
BEFORE:  qa:  A---B---C---X---R(revert of X)---M(bad merge)
                       ^                         ^
                  clean-commit                  HEAD

AFTER:   qa:  A---B---C
                       ^
                      HEAD (X, R, M gone — as if they never happened)
```

Commits stay in reflog for ~90 days (recoverable with `git reflog`).
Only this branch is affected — other branches are untouched.

### Why `--hard` and Not `--soft` or `--mixed`?

| Flag      | Working dir  | Staging     | Use when                          |
|-----------|-------------|-------------|-----------------------------------|
| `--hard`  | RESET       | RESET       | Clean slate — ready to re-merge   |
| `--soft`  | UNCHANGED   | ALL staged  | Want to review before discarding  |
| `--mixed` | UNCHANGED   | RESET       | Want files in working dir only    |

You want to throw away X, R, M completely — `--hard` is the right choice.

Tip: use `--soft` first to review, then `--hard` for real:

```bash
git reset --soft <clean-commit>
git diff --cached                        # see what's being thrown away
git reset --hard <clean-commit>          # then do it for real
```

### Why Regular Push Fails After Reset

```
After reset:

Local qa:   A---B---C              (HEAD moved backward)
Remote qa:  A---B---C---X---R---M  (still has everything)

git push origin qa         → REJECTED (local is behind remote)
git push --force origin qa → WORKS (forces remote to match local)
```

### Which Option to Choose

```
How messy is the branch?
│
├── Few conflicts, you understand each one
│   └── Option A: resolve manually (safer, no force push)
│
├── Many conflicts, hard to tell what's correct
│   └── Option B: reset and re-merge from scratch
│
└── Revert was cherry-picked across multiple branches?
    └── Option B: the revert will keep polluting future merges
        Resetting is the only way to cleanly remove it
```

---

## Why Git Revert Is Dangerous Across Branches

```
Developer reverts commit X in QA:

  QA:      ...---X---R(revert of X)
  develop: ...---X---...

Now every time you merge develop → QA (or QA → develop),
Git replays the revert R and causes conflicts with X.
```

The revert "follows" the branch — it's a commit, and merges carry
commits across branches.

| Scenario                         | Use revert?  | Better alternative              |
|----------------------------------|-------------|----------------------------------|
| Change should be permanently deleted | YES      | `git revert` is correct          |
| Temporary rollback               | NO          | Manually edit files back         |

A manual undo doesn't have the "revert propagation" problem because
Git doesn't treat it specially — it's just a commit that happens to
change code back.

---

---

________________________________________________________________________________

# Lesson Learned

When you create a feature branch from QA without adding commits,
merging that feature branch into master is the same as merging QA.
Always check what you're actually merging:

```bash
git log master..feature --oneline

# This shows ALL commits that master doesn't have yet
# If you see QA commits here, the merge will bring them too
```
