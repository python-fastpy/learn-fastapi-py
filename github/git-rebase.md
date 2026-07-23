# Git Rebase

---

## What is Rebase?

Rebase moves your branch's commits to start from a new base point.
It replays your commits one by one on top of the target branch,
creating NEW commits with the same changes but different hashes.

```
BEFORE rebase:
main:       A---B---C---D        (main moved ahead)
                 \
feature:          E---F---G      (your branch, based on B)

git checkout feature
git rebase main

AFTER rebase:
main:       A---B---C---D
                         \
feature:                  E'--F'--G'   (replayed on top of D)

E', F', G' = same changes as E, F, G but NEW hashes
```

---

## Rebase vs Merge (Side by Side)

```
MERGE (git merge):
main:       A---B---C---D---------M    (merge commit M created)
                 \               /
feature:          E---F---G-----        (all commits preserved)

Result: forked history, merge commit, original hashes preserved


REBASE (git rebase):
main:       A---B---C---D
                         \
feature:                  E'--F'--G'   (linear, replayed)

Result: linear history, no merge commit, NEW hashes
```

### Comparison Table

| Aspect              | Merge                        | Rebase                       |
|---------------------|------------------------------|------------------------------|
| History             | Forked (shows branches)      | Linear (straight line)       |
| Creates merge commit| Yes                          | No                           |
| Commit hashes       | Original preserved           | New hashes (rewritten)       |
| Safe for shared     | Yes                          | No (rewrites history)        |
| Conflict resolution | Once (at merge)              | Per commit (one at a time)   |
| Use case            | Integrating shared branches  | Cleaning up local history    |

---

## Basic Usage

```bash
# Rebase current branch onto main
git checkout feature
git rebase main

# Same thing in one command
git rebase main feature

# Rebase onto a specific commit
git rebase a1b2c3d
```

### Step-by-Step What Happens

```
git checkout feature
git rebase main

Step 1: Git finds the common ancestor (B)
main:       A---B---C---D
                 \
feature:          E---F---G

Step 2: Git saves E, F, G as patches (temporary)
patches: [E] [F] [G]

Step 3: Git moves feature pointer to tip of main (D)
main:       A---B---C---D   <-- feature now starts here
                         ^
                         feature HEAD

Step 4: Git replays patches one by one
After E:    A---B---C---D---E'
After F:    A---B---C---D---E'--F'
After G:    A---B---C---D---E'--F'--G'   <-- done
```

---

## The Golden Rule of Rebase

**NEVER rebase commits that have been pushed to a shared remote branch.**

```
DANGEROUS:
You:     A---B---C---D        (pushed to origin/feature)
Others:  A---B---C---D---X    (someone added commit X)

git rebase main

You:     A---B---E---F---C'--D'   (C and D are now C' and D' - different hashes!)
Others:  A---B---C---D---X        (still has old C and D)

Result: history has diverged, others will have merge conflicts
```

**Safe to rebase:**
- Local-only branches (not pushed yet)
- Your own feature branch that nobody else works on
- Before the first push

**Not safe to rebase:**
- Shared branches (main, develop)
- Branches others have pulled/based work on

---

## Resolving Rebase Conflicts

Unlike merge (one conflict resolution), rebase can conflict
at EACH commit being replayed.

```bash
git rebase main
# CONFLICT (content): Merge conflict in src/app.py
# error: could not apply E

# 1. See conflicted files
git status

# 2. Resolve conflicts in each file
#    (same markers: <<<, ===, >>>)

# 3. Stage resolved files
git add src/app.py

# 4. Continue to next commit
git rebase --continue
# (may conflict again at F, then at G)

# OR abort entirely (go back to before rebase)
git rebase --abort

# OR skip this commit
git rebase --skip
```

### Diagram: Conflicts During Rebase

```
Replaying E on D:  CONFLICT!  --> resolve --> git rebase --continue
Replaying F on E': OK (no conflict)
Replaying G on F': CONFLICT!  --> resolve --> git rebase --continue
Done!

result: A---B---C---D---E'--F'--G'
```

---

## Interactive Rebase (`git rebase -i`)

Rewrite, reorder, combine, or drop commits before pushing.

```bash
# Rebase last 3 commits interactively
git rebase -i HEAD~3
```

Opens editor with:
```
pick a1b2c3d commit E
pick x9y8z7w commit F
pick f1e2d3c commit G

# Commands:
# p, pick   = keep commit as-is
# r, reword = keep commit, edit message
# e, edit   = keep commit, stop to amend
# s, squash = combine with previous commit (keep message)
# f, fixup  = combine with previous commit (discard message)
# d, drop   = remove commit entirely
# reorder   = change the order of lines to reorder commits
```

### Example: Squash 3 Commits into 1

```bash
git rebase -i HEAD~3
```

Change to:
```
pick a1b2c3d commit E
squash x9y8z7w commit F
squash f1e2d3c commit G
```

Result:
```
BEFORE:  A---B---E---F---G   (3 commits)
AFTER:   A---B---EFG'        (1 combined commit)
```

### Example: Reword a Commit Message

```
pick a1b2c3d commit E
reword x9y8z7w fix typo      <-- will prompt to edit this message
pick f1e2d3c commit G
```

### Example: Reorder Commits

```
pick f1e2d3c commit G         <-- moved G first
pick a1b2c3d commit E         <-- E is now second
pick x9y8z7w commit F         <-- F is last
```

### Example: Drop a Commit

```
pick a1b2c3d commit E
drop x9y8z7w commit F         <-- F will be removed
pick f1e2d3c commit G
```

---

## Rebase --onto (Advanced)

Move a branch from one base to another.

```bash
# Move feature from develop onto main
git rebase --onto main develop feature
```

### Diagram

```
BEFORE:
main:       A---B---C
                 \
develop:          D---E
                       \
feature:                F---G

git rebase --onto main develop feature
(take commits after develop, put them on main)

AFTER:
main:       A---B---C
                 \   \
develop:          D---E
                       \
feature:          F'--G'   (now based on C, not E)
                 /
            C---
```

### Use Case: Remove Middle Commits

```
BEFORE:
main:   A---B---C---D---E---F

# Remove commits C and D, keep E and F
git rebase --onto B D

AFTER:
main:   A---B---E'--F'   (C and D removed)
```

---

## Recovering from a Bad Rebase

```bash
# BEFORE rebase, git saves the original position in reflog
git reflog
# a1b2c3d HEAD@{0}: rebase (finish): ...
# x9y8z7w HEAD@{1}: rebase (start): ...
# f1e2d3c HEAD@{2}: commit: original commit G   <-- HERE

# Go back to before the rebase
git reset --hard "HEAD@{2}"

# Or use ORIG_HEAD (git saves it automatically)
git reset --hard ORIG_HEAD
```

---

## Common Workflows

### Keep Feature Branch Up to Date

```bash
# While working on feature, main gets new commits
git checkout feature
git rebase main

# Diagram:
# BEFORE:
# main:    A---B---C---D
#               \
# feature:       E---F
#
# AFTER:
# main:    A---B---C---D
#                       \
# feature:               E'--F'

# Then when ready to merge:
git checkout main
git merge feature    # fast-forward merge (clean linear history)
```

### Clean Up Before Pushing

```bash
# Squash WIP commits into clean ones before push
git rebase -i HEAD~5

# Squash, reword, reorder as needed
# Then push
git push origin feature
```

### Pull with Rebase (Instead of Merge)

```bash
# Instead of git pull (which does fetch + merge)
git pull --rebase

# Or configure as default
git config --global pull.rebase true

# Diagram:
# Without rebase (git pull):
# main: A---B---C---M    (merge commit for pulling)
#             \     /
#              D---
#
# With rebase (git pull --rebase):
# main: A---B---C---D'   (linear, your commit replayed)
```

---

## Quick Reference

```bash
# Basic rebase
git rebase main                  # rebase current branch onto main

# Interactive
git rebase -i HEAD~3             # edit last 3 commits

# Onto
git rebase --onto main dev feat  # move feat from dev to main

# During conflicts
git rebase --continue            # after resolving
git rebase --abort               # cancel entirely
git rebase --skip                # skip this commit

# Recovery
git reset --hard ORIG_HEAD       # undo last rebase
git reflog                       # find pre-rebase state

# Pull with rebase
git pull --rebase
```

---

## Related

- [git-merge-types.md](git-merge-types.md) — merge vs rebase comparison
- [git-cherry-pick.md](git-cherry-pick.md) — picking specific commits (alternative to rebase)
- [git-merge-conflict-resolution.md](git-merge-conflict-resolution.md) — resolving rebase conflicts
