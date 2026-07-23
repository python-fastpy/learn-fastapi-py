# Git Cherry-Pick

---

## What is Cherry-Pick?

Cherry-pick copies a specific commit from one branch and applies it
to another branch. It creates a NEW commit with the same changes
but a different hash.

```
BEFORE:
main:       A---B---C
                     \
feature:              D---E---F
                          ^
                     want THIS commit on main

git checkout main
git cherry-pick E

AFTER:
main:       A---B---C---E'    (E' = new commit, same changes as E, different hash)
                     \
feature:              D---E---F    (E still exists here, unchanged)
```

---

## Basic Usage

```bash
# Cherry-pick a single commit
git checkout main
git cherry-pick a1b2c3d

# Cherry-pick multiple commits (in order)
git cherry-pick a1b2c3d x9y8z7w f1e2d3c

# Cherry-pick a range of commits (D to F inclusive)
git cherry-pick D^..F
# or
git cherry-pick D..F    # EXCLUDES D, includes E and F only

# Cherry-pick from another branch (latest commit)
git cherry-pick feature
```

### Range Diagram

```
feature:  A---B---C---D---E---F

git cherry-pick D^..F    -->  picks D, E, F (inclusive)
git cherry-pick D..F     -->  picks E, F    (excludes D)
git cherry-pick D        -->  picks D only
```

---

## Cherry-Pick Without Committing

```bash
# Apply changes but DON'T commit (stage only)
git cherry-pick --no-commit a1b2c3d
# or
git cherry-pick -n a1b2c3d

# Now you can:
git diff --cached           # review changes
git commit -m "custom msg"  # commit with your own message
# or
git reset HEAD .            # unstage if you changed your mind
```

### Diagram: Cherry-Pick with --no-commit

```
BEFORE:
main:     A---B---C

git cherry-pick -n E -n F    (apply E and F without committing)

INTERMEDIATE:
main:     A---B---C     (HEAD still here)
Staging:  [changes from E + F combined]

git commit -m "combined E and F"

AFTER:
main:     A---B---C---EF'   (one commit with both changes)
```

---

## Cherry-Pick Conflicts

```bash
# If cherry-pick conflicts:
git cherry-pick a1b2c3d
# CONFLICT (content): Merge conflict in src/app.py

# 1. See conflicted files
git status

# 2. Resolve conflicts in each file
#    (same markers as merge conflicts: <<<, ===, >>>)

# 3. Stage resolved files
git add src/app.py

# 4. Continue cherry-pick
git cherry-pick --continue

# OR abort entirely
git cherry-pick --abort

# OR skip this commit and move to next (in a range)
git cherry-pick --skip
```

### Conflict Markers in Cherry-Pick

```
<<<<<<< HEAD
// current code on your branch
const x = 1;
=======
// code from the commit you're cherry-picking
const x = 2;
>>>>>>> a1b2c3d (commit message)
```

---

## Cherry-Pick vs Merge vs Rebase

```
CHERRY-PICK: copies specific commits (surgical)
main:    A---B---C---E'         (only E copied)
              \
feature:       D---E---F

MERGE: brings ALL commits + creates merge commit
main:    A---B---C-----------M  (all of D,E,F merged)
              \             /
feature:       D---E---F---

REBASE: moves entire branch to new base (rewrites history)
feature:               D'--E'--F'   (replayed on top of C)
                      /
main:    A---B---C---
```

### Comparison Table

| Aspect              | Cherry-Pick         | Merge                | Rebase               |
|---------------------|---------------------|----------------------|----------------------|
| What it copies      | Specific commit(s)  | All commits          | All commits          |
| Creates merge commit| No                  | Yes                  | No                   |
| Preserves history   | Duplicates commits  | Preserves all        | Rewrites history     |
| Use case            | "I need just this"  | "Integrate branches" | "Clean linear history"|
| Commit hashes       | New hashes          | Original preserved   | New hashes           |
| Risk of duplicates  | Yes (same changes, different hashes) | No    | No (if done right)   |

---

## Common Use Cases

### Hotfix: Pick a Bug Fix from Feature to Main

```bash
# Bug fix is on feature branch as commit F
# Need it on main NOW, can't wait for full merge

git checkout main
git cherry-pick F

# Diagram:
# main:    A---B---C---F'        (fix applied to main)
#               \
# feature:       D---E---F---G   (fix stays here too)
```

### Backport: Pick a Fix to an Older Release

```bash
# Fix is on main, need it on release/1.0
git checkout release/1.0
git cherry-pick a1b2c3d

# Diagram:
# main:        A---B---C---FIX---D---E
# release/1.0: X---Y---Z---FIX'        (backported)
```

### Undo an Accidental Commit on Wrong Branch

```bash
# Committed on main by mistake, should be on feature
git log --oneline -1    # note the hash: a1b2c3d

# Move to feature and cherry-pick
git checkout feature
git cherry-pick a1b2c3d

# Remove from main
git checkout main
git reset --hard HEAD~1

# Diagram:
# BEFORE:
# main:    A---B---OOPS
# feature: A---B
#
# AFTER:
# main:    A---B
# feature: A---B---OOPS'
```

---

## Important: Cherry-Pick Creates Duplicate Commits

```
BEFORE cherry-pick:
main:    A---B---C
feature: A---B---D---E

git checkout main && git cherry-pick D

AFTER:
main:    A---B---C---D'    (D' has DIFFERENT hash than D, same changes)
feature: A---B---D---E     (D still here)

If you later merge feature into main:
main:    A---B---C---D'---M    (D appears TWICE in history: D and D')
                  \       /
feature:           D---E--

This is why cherry-pick should be used sparingly.
Better to merge or rebase if you want ALL commits.
```

---

## Quick Reference

```bash
# Single commit
git cherry-pick a1b2c3d

# Multiple commits
git cherry-pick a1b2c3d x9y8z7w

# Range (inclusive)
git cherry-pick D^..F

# Without committing
git cherry-pick -n a1b2c3d

# Conflict resolution
git cherry-pick --continue    # after resolving
git cherry-pick --abort       # cancel everything
git cherry-pick --skip        # skip this commit

# Edit commit message
git cherry-pick -e a1b2c3d
```

---

## Related

- [git-rebase.md](git-rebase.md) — rebase as an alternative to cherry-pick
- [git-merge-types.md](git-merge-types.md) — merge vs cherry-pick
- [git-merge-conflict-resolution.md](git-merge-conflict-resolution.md) — resolving conflicts
