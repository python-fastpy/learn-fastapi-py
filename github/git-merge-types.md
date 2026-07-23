# Git Merge Types: Understanding the Difference

Before reverting a merge, you need to know HOW the merge was done.
This changes what `git log` looks like and which revert command to use.

---

## 1. Merge Commit (`git merge`)

```bash
git checkout master
git merge feature        # creates a merge commit with 2 parents
```

```
git log --oneline --graph:

*   a1b2c3d (HEAD -> master) Merge branch 'feature' into master   <-- merge commit (2 parents)
|\
| * f1e2d3c feature commit F
| * e1d2c3b feature commit E
| * d1c2b3a feature commit D
|/
* x9y8z7w previous master commit
```

Key signs of a merge commit:
- Has TWO parent commits (shown by `|\` in graph)
- Message says "Merge branch '...' into ..."
- Feature branch commits are preserved individually
- `git cat-file -p a1b2c3d` shows two "parent" lines

### How to Revert

```bash
git revert -m 1 a1b2c3d    # -m 1 required because 2 parents
```

See [revert-master-after-merge.md](revert-master-after-merge.md) for full steps.

---

## 2. Fast-Forward Merge (`git merge` but NO merge commit created)

This happens when the target branch has NO new commits that the source
branch doesn't already have. Git just moves the pointer forward.

**WHY you see no merge commit:**

```
Example: branch1 has 2 commits, branch2 has 2 commits,
feature created from branch1, merged into branch2

CASE: branch2 is an ancestor of feature (branch2 has no unique commits)

Branch1:     A---B
                  \
Feature:           (points to B, no new commits)

Branch2:     A---B   (same history, or behind)

git checkout branch2
git merge feature

FAST-FORWARD — git just moves the branch2 pointer:
Branch2:     A---B   (already here, nothing changed, no merge commit)
```

Another common case:

```
Branch1:     A---B---C---D    (4 commits)
                          \
Feature:                   (points to D)

Branch2:     A---B            (only 2 commits, behind branch1)

git checkout branch2
git merge feature

FAST-FORWARD — branch2 pointer moves to D:
Branch2:     A---B---C---D    (pointer moved forward, no merge commit)

git log --oneline:
d1c2b3a commit D    <-- no "Merge" message, just regular commits
c1b2a3z commit C
b1a2z3y commit B
a1z2y3x commit A
```

**Fast-forward happens when:**
- The target branch (branch2) can reach feature by just moving forward
- There are NO diverging commits on the target branch
- Git sees no reason to create a merge commit

**Key signs of a fast-forward merge:**
- No "Merge branch '...'" commit in log
- No `|\` branch lines in graph
- Commits appear as if they were made directly on the branch
- `git log --merges` shows nothing

### How to FORCE a Merge Commit (Prevent Fast-Forward)

```bash
# Use --no-ff to always create a merge commit
git checkout branch2
git merge --no-ff feature

# Now you get a merge commit even if fast-forward was possible:
# *   m1e2r3g Merge branch 'feature' into branch2   <-- forced merge commit
# |\
# | * d1c2b3a commit D
# | * c1b2a3z commit C
# |/
# * b1a2z3y commit B
# * a1z2y3x commit A
```

### How to Revert a Fast-Forward (No Merge Commit to Revert)

Since there is no merge commit, you CANNOT use `git revert -m 1`.
Instead use:

```bash
# Option 1: git reset (if you know where branch2 was before)
git checkout branch2
git log --oneline          # find the commit branch2 was at before merge
git reset --hard b1a2z3y   # reset to where branch2 was (commit B)

# Option 2: git reflog (to find where branch2 was before the merge)
git reflog
# output:
# d1c2b3a HEAD@{0}: merge feature: Fast-forward     <-- the fast-forward
# b1a2z3y HEAD@{1}: checkout: moving to branch2      <-- branch2 was HERE
git reset --hard "HEAD@{1}"    # MUST use quotes (see git-reflog-recovery.md)
```

### Comparison: Why No Merge Commit vs Merge Commit

```
FAST-FORWARD (no merge commit):
Branch2 before:  A---B
Feature:         A---B---C---D
                 Branch2 has nothing unique, just move pointer
Branch2 after:   A---B---C---D    (no merge commit)

REAL MERGE (merge commit created):
Branch2 before:  A---B---E---F    (has unique commits E, F)
Feature:         A---B---C---D    (has unique commits C, D)
                 Both have unique work, must create merge commit
Branch2 after:   A---B---E---F---M
                          \     /
                           C---D
```

---

## 3. Squash Merge (`git merge --squash`)

```bash
git checkout master
git merge --squash feature    # squashes all into one commit
git commit -m "add feature"
```

```
git log --oneline --graph:

* b2c3d4e (HEAD -> master) add feature    <-- single commit (1 parent, NOT a merge commit)
* x9y8z7w previous master commit
```

Key signs of a squash merge:
- Has ONE parent (regular linear commit)
- No branch lines in graph
- All feature changes collapsed into one commit
- Does NOT need `-m 1` flag when reverting

### How to Revert

```bash
git revert b2c3d4e    # no -m needed, only one parent
```

---

## How to Check Which Type You Have

```bash
# Check number of parents for a commit
git cat-file -p a1b2c3d | grep parent

# TWO parent lines = merge commit
# parent x9y8z7w    <-- master side
# parent f1e2d3c    <-- feature side

# ONE parent line = squash merge or regular commit
# parent x9y8z7w

# NO merge commit at all = fast-forward merge
# git log --merges shows nothing
```

See [git-cat-file.md](git-cat-file.md) for full `git cat-file` explanation.

---

## Comparison of All Merge Types

| Aspect                | Merge Commit          | Fast-Forward            | Squash Merge            |
|-----------------------|-----------------------|-------------------------|-------------------------|
| Creates merge commit? | YES (2 parents)       | NO                      | NO (1 parent)           |
| Preserves commits?    | Yes, individually     | Yes, individually       | No, collapsed into one  |
| Shows in graph?       | `\|\ ` branch lines  | Linear, no branches     | Linear, no branches     |
| `git log --merges`    | Shows the merge       | Shows nothing           | Shows nothing           |
| Revert command        | `git revert -m 1`     | `git reset --hard`      | `git revert` (no -m)   |
| Needs `-m` flag?      | YES                   | N/A (no merge commit)   | NO                      |

---

## Why Merge Commit Revert Needs `-m 1` but Squash Doesn't

```
MERGE COMMIT (2 parents):
*   a1b2c3d Merge branch 'feature'    <-- which parent to keep? git doesn't know
|\
| * f1e2d3c feature side              <-- parent 2
|/
* x9y8z7w master side                 <-- parent 1

git revert a1b2c3d          # ERROR: "is a merge but no -m option was given"
git revert -m 1 a1b2c3d     # WORKS: keep parent 1 (master), undo parent 2 (feature)


SQUASH COMMIT (1 parent):
* b2c3d4e add feature                 <-- only 1 parent, no ambiguity
* x9y8z7w master side

git revert b2c3d4e           # WORKS: no -m needed, only one parent
```
