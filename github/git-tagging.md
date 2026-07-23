# Git Tagging

---

## What is a Tag?

A tag is a permanent label pointing to a specific commit.
Unlike branches, tags don't move — they always point to the same commit.

```
Branches move:                Tags don't:
main: A---B---C---D           v1.0        v2.0
           ^       ^           |            |
          was     now          v            v
                              A---B---C---D---E---F
                                             ^
                                            v2.1 (stays here forever)
```

---

## Two Types of Tags

### 1. Lightweight Tag (Just a Pointer)

```bash
# Like a branch that doesn't move — just a name pointing to a commit
git tag v1.0
```

```
Stored as: .git/refs/tags/v1.0
Contains:  a1b2c3d  (just the commit hash, nothing else)
```

### 2. Annotated Tag (Full Tag Object)

```bash
# Stores tagger name, email, date, message — like a commit object
git tag -a v1.0 -m "Release version 1.0"
```

```
Stored as: a full git object with:
  - Tag name: v1.0
  - Tagger: John Doe <john@example.com>
  - Date: 2026-07-23
  - Message: Release version 1.0
  - Points to: commit a1b2c3d
```

### Comparison

| Aspect           | Lightweight           | Annotated              |
|------------------|-----------------------|------------------------|
| Storage          | Just a pointer        | Full git object        |
| Has message?     | No                    | Yes                    |
| Has author?      | No                    | Yes (tagger)           |
| Has date?        | No                    | Yes                    |
| Can be signed?   | No                    | Yes (GPG)              |
| Use case         | Personal/temporary    | Releases, shared tags  |
| Command          | `git tag v1.0`        | `git tag -a v1.0 -m "msg"` |

**Recommendation:** Use annotated tags for releases (has metadata).
Use lightweight for local bookmarks.

---

## Create Tags

```bash
# Lightweight tag on current commit
git tag v1.0

# Annotated tag on current commit
git tag -a v1.0 -m "Release 1.0 - initial release"

# Tag a specific older commit
git tag -a v0.9 -m "Beta release" a1b2c3d

# Tag with the editor (opens editor for message)
git tag -a v1.0
```

### Diagram: Tagging a Release

```
main:  A---B---C---D---E---F---G

git tag -a v1.0 -m "first release" C
git tag -a v2.0 -m "second release" F

main:  A---B---C---D---E---F---G
                ^           ^
               v1.0        v2.0
```

---

## List Tags

```bash
# List all tags
git tag
# v1.0
# v1.1
# v2.0

# List tags with pattern
git tag -l "v1.*"
# v1.0
# v1.1

# List tags with messages (annotated only)
git tag -n
# v1.0    Release 1.0 - initial release
# v2.0    Release 2.0 - new features

# List tags sorted by version (semantic version sort)
git tag -l --sort=version:refname
# v1.0
# v1.1
# v1.10    (correctly after v1.9, not after v1.1)
# v2.0

# Show tag details
git show v1.0
# tag v1.0
# Tagger: John Doe <john@example.com>
# Date:   Wed Jul 23 2026
#
# Release 1.0 - initial release
#
# commit a1b2c3d...
# (shows the commit diff)
```

---

## Push Tags to Remote

Tags are NOT pushed by default. You must push them explicitly.

```bash
# Push a specific tag
git push origin v1.0

# Push ALL tags
git push origin --tags

# Push only annotated tags (not lightweight)
git push origin --follow-tags
```

### Diagram: Local vs Remote Tags

```
LOCAL:   A---B---C---D
               ^     ^
              v1.0  v1.1

REMOTE:  A---B---C---D    (no tags until you push them)

git push origin --tags

REMOTE:  A---B---C---D
               ^     ^
              v1.0  v1.1   (now tags exist on remote)
```

---

## Delete Tags

```bash
# Delete a local tag
git tag -d v1.0
# Deleted tag 'v1.0' (was a1b2c3d)

# Delete a remote tag
git push origin --delete v1.0
# or
git push origin :refs/tags/v1.0
```

---

## Checkout a Tag

```bash
# Checkout a tag (detached HEAD state)
git checkout v1.0
# You are in 'detached HEAD' state...

# Create a branch from a tag (to make changes)
git checkout -b hotfix-v1.0 v1.0
```

### Diagram: Detached HEAD

```
git checkout v1.0

main:    A---B---C---D---E    (main keeps going)
                ^
               v1.0
                ^
               HEAD   (detached — not on any branch)

Any commits here will be LOST unless you create a branch:
git checkout -b fix-from-v1.0
```

---

## Semantic Versioning with Tags

```
v MAJOR . MINOR . PATCH
v 2     . 1     . 3

MAJOR = breaking changes (v1.0 -> v2.0)
MINOR = new features, backward compatible (v1.0 -> v1.1)
PATCH = bug fixes (v1.0.0 -> v1.0.1)
```

### Common Tag Patterns

```bash
# Release tags
git tag -a v1.0.0 -m "Initial release"
git tag -a v1.0.1 -m "Bug fix: login crash"
git tag -a v1.1.0 -m "Feature: dark mode"
git tag -a v2.0.0 -m "Breaking: new API"

# Pre-release tags
git tag -a v2.0.0-beta.1 -m "Beta 1"
git tag -a v2.0.0-rc.1 -m "Release candidate 1"

# Timeline:
# v1.0.0 --- v1.0.1 --- v1.1.0 --- v2.0.0-beta.1 --- v2.0.0-rc.1 --- v2.0.0
```

---

## Common Workflows

### Release Workflow

```bash
# 1. Finish all work for the release
git checkout main
git pull

# 2. Tag the release
git tag -a v1.2.0 -m "Release 1.2.0 - user profiles feature"

# 3. Push tag
git push origin v1.2.0

# 4. GitHub/GitLab will show this as a release
```

### Find Which Tag Contains a Commit

```bash
# Which tags contain commit a1b2c3d?
git tag --contains a1b2c3d

# What's the latest tag reachable from HEAD?
git describe --tags
# output: v1.2.0-5-ga1b2c3d
#          ^      ^  ^
#          |      |  commit hash
#          |      5 commits since v1.2.0
#          latest tag
```

### Compare Two Tags

```bash
# Commits between v1.0 and v2.0
git log v1.0..v2.0 --oneline

# Files changed between tags
git diff v1.0..v2.0 --stat

# Generate changelog
git log v1.0..v2.0 --oneline --no-merges
```

---

## Quick Reference

```bash
# Create
git tag v1.0                        # lightweight
git tag -a v1.0 -m "message"        # annotated
git tag -a v1.0 a1b2c3d             # tag specific commit

# List
git tag                             # all tags
git tag -l "v1.*"                   # pattern match
git tag -n                          # with messages

# Push
git push origin v1.0                # single tag
git push origin --tags              # all tags

# Delete
git tag -d v1.0                     # local
git push origin --delete v1.0       # remote

# Checkout
git checkout v1.0                   # detached HEAD
git checkout -b branch v1.0         # new branch from tag

# Info
git show v1.0                       # tag details
git describe --tags                  # nearest tag
git log v1.0..v2.0 --oneline        # changes between tags
```

---

## Related

- [git-branching.md](git-branching.md) — branches vs tags
- [git-reset-vs-revert.md](git-reset-vs-revert.md) — going back to a tagged state
