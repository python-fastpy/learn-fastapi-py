# All Commands to Get Parents of a Commit

---

## 8 Methods to Get Parent Hashes

```bash
# -------------------------------------------------------
# Method 1: git cat-file -p (raw commit data, most detailed)
# -------------------------------------------------------
git cat-file -p a1b2c3d
# output:
# tree 4b825dc6...
# parent x9y8z7w       <-- Parent 1 (master)
# parent f1e2d3c       <-- Parent 2 (feature)
# author ...
# committer ...
# Merge branch 'feature' into master

# Show ONLY parent lines:
git cat-file -p a1b2c3d | grep parent
# parent x9y8z7w       <-- Parent 1
# parent f1e2d3c       <-- Parent 2

# -------------------------------------------------------
# Method 2: git log --pretty=format:"%P" (parent hashes only)
# -------------------------------------------------------
git log --pretty=format:"%P" -1 a1b2c3d
# output: x9y8z7w f1e2d3c
#          ^           ^
#          Parent 1    Parent 2

# -------------------------------------------------------
# Method 3: git show (similar to log, shows parents)
# -------------------------------------------------------
git show --format="%P" -s a1b2c3d
# output: x9y8z7w f1e2d3c

# -------------------------------------------------------
# Method 4: git rev-parse (get specific parent by number)
# -------------------------------------------------------
# Get Parent 1 (master side):
git rev-parse a1b2c3d^1
# output: x9y8z7w

# Get Parent 2 (feature side):
git rev-parse a1b2c3d^2
# output: f1e2d3c

# -------------------------------------------------------
# Method 5: git log --graph (visual, shows parent relationship)
# -------------------------------------------------------
git log --oneline --graph -5
# *   a1b2c3d Merge branch 'feature' into master
# |\
# | * f1e2d3c feature commit    <-- Parent 2 (RIGHT side)
# |/
# * x9y8z7w master commit       <-- Parent 1 (LEFT side)

# -------------------------------------------------------
# Method 6: git log with parent hashes and commit info together
# -------------------------------------------------------
git log --pretty=format:"commit: %H | parents: %P | message: %s" -1 a1b2c3d
# output: commit: a1b2c3d... | parents: x9y8z7w... f1e2d3c... | message: Merge branch 'feature'

# -------------------------------------------------------
# Method 7: git show with full parent details
# -------------------------------------------------------
git show --stat a1b2c3d
# commit a1b2c3d
# Merge: x9y8z7w f1e2d3c      <-- shows both parents right here
# Author: ...
# Date: ...
#
#     Merge branch 'feature' into master
#
#  file1.py | 10 ++++
#  file2.py |  5 +++

# -------------------------------------------------------
# Method 8: git log format placeholders for parents
# -------------------------------------------------------
# %P = full parent hashes (space separated)
# %p = short parent hashes (space separated)
# %H = full commit hash
# %h = short commit hash

git log --pretty=format:"short parents: %p" -1 a1b2c3d
# output: short parents: x9y8z7w f1e2d3c

git log --pretty=format:"full parents: %P" -1 a1b2c3d
# output: full parents: x9y8z7wabcdef1234 f1e2d3cabcdef5678
```

---

## Quick Cheat Sheet

```
FASTEST (just parent hashes):
  git rev-parse a1b2c3d^1        --> Parent 1 hash
  git rev-parse a1b2c3d^2        --> Parent 2 hash

READABLE (shows "Merge: hash1 hash2"):
  git show --stat a1b2c3d

ONE-LINER (both parents):
  git log --pretty=format:"%p" -1 a1b2c3d

RAW DATA (everything):
  git cat-file -p a1b2c3d

VISUAL:
  git log --oneline --graph -5
```

---

## How to Know Which Parent is Master vs Feature

The parent order is determined by HOW you ran the merge:

```bash
git checkout master        # you were ON master        --> this becomes Parent 1
git merge feature          # you merged IN feature     --> this becomes Parent 2
```

- **Parent 1 (-m 1)** = the branch you were **standing on** when you ran `git merge` (master)
- **Parent 2 (-m 2)** = the branch you **merged in** (feature)

This order is fixed at merge time and never changes.

### 5 Ways to Identify Which Parent is Which

```bash
# Method 1: git cat-file (parents listed in order)
git cat-file -p a1b2c3d
# parent x9y8z7w      <-- Parent 1 (branch you were ON = master)
# parent f1e2d3c      <-- Parent 2 (branch you merged IN = feature)

# Method 2: git log --pretty (space separated, in order)
git log --pretty=format:"%P" -1 a1b2c3d
# output: x9y8z7w f1e2d3c
#          ^           ^
#          Parent 1    Parent 2

# Method 3: git show (shows "Merge: hash1 hash2")
git show --format="%P" -s a1b2c3d
# output: x9y8z7w f1e2d3c

# Method 4: Verify by checking what each parent hash points to
git log --oneline -1 x9y8z7w    # shows a master commit
git log --oneline -1 f1e2d3c    # shows a feature/QA commit

# Method 5: git log --graph (visual)
git log --oneline --graph -5
# *   a1b2c3d Merge branch 'feature' into master
# |\
# | * f1e2d3c feature commit    <-- right side = Parent 2 (feature)
# |/
# * x9y8z7w master commit       <-- left side  = Parent 1 (master)
#
# LEFT line  = Parent 1 (master)  = -m 1
# RIGHT line = Parent 2 (feature) = -m 2
```

### Reading the Commit Message

The merge commit message itself tells you which branch was merged:

```
"Merge branch 'feature' into master"
                ^                ^
                |                |
         branch merged IN    branch you were ON
         (Parent 2)          (Parent 1)
```

If it says just `"Merge branch 'feature'"` (without "into ..."),
it means you were on the default branch (master/main).

---

## Summary

```
git checkout master   &&   git merge feature

Parent 1 = master  = -m 1 = LEFT side in graph  = the one you KEEP when reverting
Parent 2 = feature = -m 2 = RIGHT side in graph = the one you UNDO when reverting

So: git revert -m 1 a1b2c3d
    means: "keep master (parent 1), undo feature (parent 2)"
```

---

## Related

- [git-cat-file.md](git-cat-file.md) — full explanation of `git cat-file -p`
- [git-merge-types.md](git-merge-types.md) — merge commit vs fast-forward vs squash
- [revert-master-after-merge.md](revert-master-after-merge.md) — how to revert merges
