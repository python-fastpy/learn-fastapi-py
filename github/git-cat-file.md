# Understanding `git cat-file -p`

`git cat-file -p` prints the raw internal data of any git object.
When used on a commit hash, it shows everything git stores about that commit.

---

## Full Output Explained

```bash
git cat-file -p a1b2c3d
```

Output for a **merge commit**:
```
tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904    <-- snapshot of all files at this commit
parent x9y8z7w                                    <-- Parent 1: branch you were ON (master)
parent f1e2d3c                                    <-- Parent 2: branch you merged IN (feature)
author John Doe <john@example.com> 1690000000 +0530    <-- who wrote the code
committer John Doe <john@example.com> 1690000000 +0530  <-- who created the commit

Merge branch 'feature' into master                <-- commit message
```

Output for a **regular commit** (or squash merge):
```
tree 5c926dc742cb6eb9a060e54bf8d69288fbee4905    <-- snapshot of all files
parent x9y8z7w                                    <-- only ONE parent
author John Doe <john@example.com> 1690000000 +0530
committer John Doe <john@example.com> 1690000000 +0530

add feature                                       <-- commit message
```

---

## What Each Field Means

```
tree      = pointer to the file tree (snapshot of ALL files at this point)
parent    = pointer to the previous commit(s)
            - 1 parent  = regular commit or squash merge
            - 2 parents = merge commit
            - 0 parents = initial/root commit (first ever commit)
author    = person who originally wrote the changes
committer = person who applied the commit (can differ in cherry-pick, rebase)
message   = the commit message text
```

---

## Useful Variations

```bash
# Show full commit data
git cat-file -p a1b2c3d

# Show ONLY parents
git cat-file -p a1b2c3d | grep parent

# Show the type of a git object (commit, tree, blob, tag)
git cat-file -t a1b2c3d
# output: commit

# Show size of the object
git cat-file -s a1b2c3d
# output: 312   (bytes)

# Show the file tree at that commit
git cat-file -p a1b2c3d | grep tree
# tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904
# Then inspect that tree:
git cat-file -p 4b825dc642cb6eb9a060e54bf8d69288fbee4904
# output: list of files and folders at that commit
```

---

## Git Object Types

`git cat-file` works on any git object, not just commits:

```bash
# Check what type an object is
git cat-file -t <hash>

# Types:
# commit  = a commit (what we mostly use)
# tree    = a directory listing (files and subdirectories)
# blob    = file contents
# tag     = an annotated tag
```

### Inspecting a Tree (Directory Listing)

```bash
# Get the tree hash from a commit
git cat-file -p a1b2c3d | grep tree
# tree 4b825dc6...

# Inspect the tree
git cat-file -p 4b825dc6...
# output:
# 100644 blob 8a7b3c...    .gitignore
# 100644 blob 9d4e5f...    README.md
# 040000 tree 1a2b3c...    src/
# 100644 blob 5f6g7h...    package.json

# 100644 = regular file
# 040000 = directory (tree)
# blob   = file contents
# tree   = subdirectory
```

### Inspecting a Blob (File Contents)

```bash
# Get file contents at a specific commit
git cat-file -p 8a7b3c...
# output: actual contents of .gitignore at that commit
```

---

## Practical Uses

```bash
# Check if a commit is a merge commit
git cat-file -p a1b2c3d | grep parent
# 2 parent lines = merge commit
# 1 parent line  = regular/squash commit

# See who authored vs who committed (differs in cherry-pick/rebase)
git cat-file -p a1b2c3d | grep -E "author|committer"

# View a file at a specific commit without checking out
git cat-file -p a1b2c3d:src/app.py
# output: contents of src/app.py as it was at commit a1b2c3d

# Compare: what git stores vs what you see
# git log    = formatted, human-readable view
# cat-file   = raw internal data (what git actually stores)
```

---

## Related

- [git-commit-parents.md](git-commit-parents.md) — all commands to get parent commits
- [git-merge-types.md](git-merge-types.md) — how to identify merge type using cat-file
