# Git Stash

---

## What is Stash?

Stash saves your uncommitted changes (staged + unstaged) temporarily,
giving you a clean working directory. Like putting your work in a drawer.

```
BEFORE stash:
Working Dir:   file.py (modified)    utils.py (modified)
Staging Area:  app.py (staged)
                |
                v
git stash
                |
                v
AFTER stash:
Working Dir:   CLEAN (matches last commit)
Staging Area:  CLEAN
Stash Stack:   stash@{0} = your saved changes
```

---

## Basic Usage

```bash
# Save all changes (staged + unstaged) to stash
git stash

# Same as above but with a descriptive message
git stash save "work in progress on login page"
# or (modern syntax)
git stash push -m "work in progress on login page"

# Restore the most recent stash (removes from stash stack)
git stash pop

# Restore the most recent stash (keeps it in stash stack)
git stash apply
```

### Diagram: stash → switch → pop

```
feature branch:  A---B---[uncommitted work]
                         |
                    git stash        <-- saves work, cleans directory
                         |
                    git switch main  <-- now safe to switch
                         |
                    (do some work on main)
                         |
                    git switch feature
                         |
                    git stash pop    <-- restores work
                         |
feature branch:  A---B---[uncommitted work is back]
```

---

## List Stashes

```bash
git stash list
# output:
# stash@{0}: WIP on feature: a1b2c3d add login    <-- most recent
# stash@{1}: On main: x9y8z7w fix bug              <-- older
# stash@{2}: On develop: work in progress           <-- oldest
```

### Stash Stack Diagram

```
stash@{0}  <-- TOP (most recent, what pop/apply uses by default)
stash@{1}
stash@{2}  <-- BOTTOM (oldest)

git stash       --> pushes to TOP
git stash pop   --> pops from TOP
```

---

## Apply a Specific Stash

```bash
# Apply a specific stash (by index)
git stash apply stash@{1}

# Pop a specific stash
git stash pop stash@{2}

# IMPORTANT: wrap in quotes on PowerShell/Zsh
git stash apply "stash@{1}"
```

---

## Stash with Options

```bash
# Stash INCLUDING untracked files (new files not yet git add'ed)
git stash -u
# or
git stash --include-untracked

# Stash INCLUDING ignored files too
git stash -a
# or
git stash --all

# Stash ONLY specific files
git stash push -m "stash only app.py" src/app.py src/utils.py

# Stash everything EXCEPT staged files (keep staged as-is)
git stash --keep-index
```

### Diagram: What Gets Stashed

```
git stash          -->  stashes: staged + unstaged modified files
                        ignores: untracked files, ignored files

git stash -u       -->  stashes: staged + unstaged + untracked
                        ignores: ignored files

git stash -a       -->  stashes: staged + unstaged + untracked + ignored
                        (everything)

git stash --keep-index  -->  stashes: unstaged only
                              keeps:  staged files stay in staging area
```

---

## View Stash Contents

```bash
# Show files changed in most recent stash
git stash show
# output:
#  src/app.py   | 10 +++++-----
#  src/utils.py |  3 +++

# Show actual diff (code changes)
git stash show -p

# Show diff for a specific stash
git stash show -p stash@{1}

# Show files in a stash
git stash show --stat stash@{0}
```

---

## Delete Stashes

```bash
# Drop a specific stash
git stash drop stash@{1}

# Drop the most recent stash
git stash drop

# Delete ALL stashes (CAREFUL: no recovery)
git stash clear
```

---

## Create a Branch from Stash

If your stash conflicts with current changes, create a branch from it:

```bash
git stash branch new-feature-branch stash@{0}

# This does:
# 1. Creates new branch from the commit where you stashed
# 2. Applies the stash
# 3. Drops the stash if applied successfully
```

### Diagram

```
BEFORE:
main:    A---B---C---D   (current, stash was made at B)

git stash branch new-branch stash@{0}

AFTER:
main:        A---B---C---D
                  \
new-branch:        B + [stash changes applied]
```

---

## Stash Conflicts

```bash
# If stash pop/apply conflicts:
git stash pop
# CONFLICT (content): Merge conflict in src/app.py

# Resolve the conflict (same as merge conflict):
# 1. Edit the conflicted files
# 2. Remove conflict markers (<<<, ===, >>>)
# 3. Stage resolved files
git add src/app.py

# NOTE: after a conflicted pop, the stash is NOT dropped
# You must manually drop it:
git stash drop
```

---

## Common Patterns

### Quick Context Switch

```bash
# Save current work
git stash -m "feature: half-done login form"

# Switch branches, do urgent fix
git switch main
# ... fix bug, commit, push ...

# Come back and restore
git switch feature
git stash pop
```

### Testing Clean State

```bash
# Stash everything to test a clean build
git stash -u
npm run build         # test with clean working directory
git stash pop         # restore everything
```

### Partial Stash (Interactive)

```bash
# Stash only some changes interactively
git stash -p
# Git will show each change and ask:
# Stash this hunk [y,n,q,a,d,/,s,e,?]?
# y = yes, stash this chunk
# n = no, skip this chunk
# s = split into smaller chunks
# q = quit (stash what was selected so far)
```

---

## Quick Reference

```bash
# Save
git stash                          # staged + unstaged
git stash -u                       # + untracked files
git stash push -m "message"        # with description
git stash push file1.py file2.py   # specific files only

# Restore
git stash pop                      # restore + remove from stack
git stash apply                    # restore + keep in stack
git stash apply "stash@{2}"        # specific stash

# View
git stash list                     # list all stashes
git stash show                     # files changed
git stash show -p                  # actual diff

# Delete
git stash drop                     # most recent
git stash drop "stash@{1}"         # specific
git stash clear                    # all (no recovery)

# Branch
git stash branch new-branch        # create branch from stash
```

---

## Related

- [git-branching.md](git-branching.md) — switching branches (when you need stash)
- [git-merge-conflict-resolution.md](git-merge-conflict-resolution.md) — resolving stash conflicts
