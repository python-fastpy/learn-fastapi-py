# Git Reset vs Revert

---

## Overview

Both undo changes, but in fundamentally different ways.

```
REVERT: Creates a NEW commit that undoes an old commit (safe)
main:   A---B---C---C'     (C' undoes C, history preserved)

RESET:  Moves HEAD backward, as if commits never happened (destructive)
main:   A---B               (C is gone from history)
```

---

## git revert (Safe — Preserves History)

Creates a new commit that does the **opposite** of a previous commit.

```bash
git revert a1b2c3d
```

### Diagram

```
BEFORE:
main:   A---B---C---D---E    (want to undo C)
                ^
                undo this

git revert C

AFTER:
main:   A---B---C---D---E---C'   (C' reverses C's changes)
                                  (C still in history)
```

### Key Points
- **Adds** a new commit (doesn't remove old ones)
- History is preserved — everyone can see what was undone
- Safe for shared branches — no force push needed
- Works on any commit, not just the latest

```bash
# Revert latest commit
git revert HEAD

# Revert a specific commit
git revert a1b2c3d

# Revert without committing (stage only)
git revert --no-commit a1b2c3d

# Revert a merge commit (needs -m flag)
git revert -m 1 a1b2c3d
```

---

## git reset (Destructive — Rewrites History)

Moves HEAD and branch pointer backward. Has 3 modes that control
what happens to the changes.

### The 3 Modes

```
                    HEAD     Index      Working Dir
                  (commit)  (staging)   (files on disk)
                  --------  ---------  ---------------
--soft              moves    UNCHANGED   UNCHANGED      (changes stay staged)
--mixed (default)   moves    RESET       UNCHANGED      (changes stay unstaged)
--hard              moves    RESET       RESET          (everything gone)
```

### Diagram: All 3 Modes

```
BEFORE (3 commits: A, B, C):

Commit History:   A---B---C   (HEAD at C)
Staging Area:     [matches C]
Working Dir:      [matches C]

--- git reset --soft B ---

Commit History:   A---B       (HEAD moved to B, C removed from history)
Staging Area:     [C's changes are staged]    <-- KEPT
Working Dir:      [C's changes in files]      <-- KEPT

--- git reset --mixed B --- (or just: git reset B)

Commit History:   A---B       (HEAD moved to B)
Staging Area:     [matches B]                 <-- RESET
Working Dir:      [C's changes in files]      <-- KEPT (unstaged)

--- git reset --hard B ---

Commit History:   A---B       (HEAD moved to B)
Staging Area:     [matches B]                 <-- RESET
Working Dir:      [matches B]                 <-- RESET (changes GONE)
```

---

## Side-by-Side Comparison

```
Scenario: undo commit C

git revert C:
  History BEFORE:  A---B---C
  History AFTER:   A---B---C---C'    (C' added, C still exists)
  Staging:         clean
  Working Dir:     clean
  Need force push: NO

git reset --hard B:
  History BEFORE:  A---B---C
  History AFTER:   A---B              (C is gone)
  Staging:         clean
  Working Dir:     clean
  Need force push: YES

git reset --soft B:
  History BEFORE:  A---B---C
  History AFTER:   A---B              (C is gone from history)
  Staging:         C's changes staged (ready to re-commit)
  Working Dir:     C's changes present
  Need force push: YES

git reset --mixed B:
  History BEFORE:  A---B---C
  History AFTER:   A---B              (C is gone from history)
  Staging:         clean
  Working Dir:     C's changes present (unstaged)
  Need force push: YES
```

---

## Full Comparison Table

| Aspect              | `git revert`         | `git reset --soft`   | `git reset --mixed`  | `git reset --hard`   |
|---------------------|----------------------|----------------------|----------------------|----------------------|
| Changes history     | No (adds commit)     | Yes (removes commits)| Yes (removes commits)| Yes (removes commits)|
| Safe for shared     | Yes                  | No                   | No                   | No                   |
| Force push needed   | No                   | Yes                  | Yes                  | Yes                  |
| Changes in staging  | No                   | Yes (kept staged)    | No (unstaged)        | No (deleted)         |
| Changes in work dir | No                   | Yes (kept)           | Yes (kept unstaged)  | No (deleted)         |
| Can undo any commit | Yes                  | Only recent (linear) | Only recent (linear) | Only recent (linear) |
| Can cause conflicts | Yes                  | No                   | No                   | No                   |
| Recoverable         | Always               | Via reflog           | Via reflog           | Via reflog (risky)   |

---

## When to Use Which

```
Decision Tree:

Has the commit been pushed to a shared branch?
│
├── YES
│   └── Use git revert (safe, no force push)
│
└── NO (local only)
    │
    ├── Want to keep the changes for editing?
    │   ├── Keep staged   --> git reset --soft
    │   └── Keep unstaged --> git reset --mixed
    │
    ├── Want to completely discard everything?
    │   └── git reset --hard
    │
    └── Want to undo a specific older commit (not the latest)?
        └── Use git revert (reset can only go back linearly)
```

---

## Undoing the Last N Commits

```bash
# Undo last 1 commit (keep changes staged)
git reset --soft HEAD~1

# Undo last 3 commits (keep changes unstaged)
git reset HEAD~3

# Undo last 1 commit (discard all changes)
git reset --hard HEAD~1

# Undo last 1 commit with revert (safe)
git revert HEAD
```

### Diagram: HEAD~N

```
main:   A---B---C---D---E   (HEAD = E)

HEAD~1 = D
HEAD~2 = C
HEAD~3 = B

git reset --hard HEAD~2   -->   main: A---B---C   (D, E removed)
```

---

## Reverting a Revert

If you revert a commit and later want the changes back:

```bash
# Original revert
git revert a1b2c3d    # creates C'

# Undo the revert (revert the revert)
git revert <C'-hash>  # creates C''

# Diagram:
# main: A---B---C---C'---C''
#                    ^     ^
#                 undid C  undid the undo (C is back)
```

---

## Reset After Accidental Commit

```bash
# Oops, committed to wrong branch
git log --oneline -1    # note: a1b2c3d

# Undo the commit but keep changes
git reset --soft HEAD~1

# Now move to correct branch
git stash
git checkout correct-branch
git stash pop
git commit -m "right place now"
```

### Diagram

```
BEFORE:
main:    A---B---OOPS       (committed here by mistake)

git reset --soft HEAD~1

AFTER:
main:    A---B              (OOPS removed, changes still staged)
staging: [OOPS changes]

git stash && git checkout feature && git stash pop && git commit

feature: X---Y---OOPS'     (changes now on correct branch)
```

---

## Common Patterns

### Uncommit (Keep Changes)

```bash
git reset --soft HEAD~1     # undo commit, keep staged
git reset HEAD~1            # undo commit, keep unstaged
```

### Unstage Files

```bash
git reset HEAD file.py      # unstage a specific file
git reset HEAD .            # unstage everything
```

### Discard All Local Changes

```bash
git reset --hard HEAD       # discard all uncommitted changes
git clean -fd               # also remove untracked files
```

### Squash Last N Commits

```bash
git reset --soft HEAD~3     # undo last 3 commits (keep staged)
git commit -m "combined"    # recommit as one
```

---

## Quick Reference

```bash
# REVERT (safe)
git revert HEAD                   # undo last commit
git revert a1b2c3d                # undo specific commit
git revert -m 1 a1b2c3d           # undo merge commit
git revert --no-commit a1b2c3d    # stage only, don't commit

# RESET
git reset --soft HEAD~1           # undo commit, keep staged
git reset HEAD~1                  # undo commit, keep unstaged
git reset --hard HEAD~1           # undo commit, discard all
git reset HEAD file.py            # unstage a file

# RECOVERY
git reflog                        # find lost commits
git reset --hard "HEAD@{1}"       # go back to reflog entry
```

---

## Related

- [revert-master-after-merge.md](revert-master-after-merge.md) — reverting merge commits
- [git-commit-parents.md](git-commit-parents.md) — understanding -m 1 flag
- [git-merge-conflict-resolution.md](git-merge-conflict-resolution.md) — conflicts during revert
