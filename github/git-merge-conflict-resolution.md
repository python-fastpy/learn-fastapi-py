# Git Merge Conflict Resolution (During Revert)

---

## When Does `git revert -m 1` Give Conflicts?

Conflicts happen when files changed by the merge were ALSO modified
by later commits on master. Git can't automatically decide which
version to keep.

```
Master: X---Y---Z---M---N---O   (commits N, O modified same files that M brought in)
                     ^
                     trying to revert this, but N and O touched the same lines
```

---

## Step-by-Step: How to Resolve

```bash
# 1. Run the revert (it will pause with conflicts)
git revert -m 1 a1b2c3d
# output:
# CONFLICT (content): Merge conflict in src/app.py
# CONFLICT (content): Merge conflict in src/utils.py
# error: could not revert a1b2c3d

# 2. See which files have conflicts
git status
# output:
# Unmerged paths:
#   both modified:   src/app.py
#   both modified:   src/utils.py

# 3. Open each conflicted file — you'll see conflict markers (explained below)
```

---

## Reading Conflict Markers

When you open a conflicted file, you'll see:

```
<<<<<<< HEAD
// This is the CURRENT code on master (after commits N, O)
// This is what master looks like RIGHT NOW
const result = processData(input, options);
=======
// This is what the revert WANTS to change it to
// (the state BEFORE the merge happened)
const result = processData(input);
>>>>>>> parent of a1b2c3d (Merge branch 'feature')
```

What each marker means:

```
<<<<<<< HEAD        = START of current master code
                      (KEEP this section if you want the current state)

=======             = SEPARATOR between the two versions

>>>>>>> parent ...  = END of what the revert wants
                      (KEEP this section if you want pre-merge state)
```

---

## 4 Approaches to Resolve Each File

```bash
# APPROACH A: Keep the revert's version (go back to pre-merge state)
#   - Remove everything between <<<<<<< HEAD and =======
#   - Keep everything between ======= and >>>>>>>
#   - Delete the marker lines themselves (<<<, ===, >>>)

# APPROACH B: Keep current master version (ignore the revert for this file)
#   - Keep everything between <<<<<<< HEAD and =======
#   - Remove everything between ======= and >>>>>>>
#   - Delete the marker lines themselves

# APPROACH C: Manually combine both (custom resolution)
#   - Edit the file to be exactly what you want
#   - Delete all marker lines (<<<, ===, >>>)

# APPROACH D: Use git checkout to pick a whole file
git checkout --ours src/app.py      # keep current master version
git checkout --theirs src/app.py    # keep the revert's version (pre-merge)
```

### Understanding `--ours` vs `--theirs` in a Revert

During a REVERT (not a merge), the meaning is:

```
--ours   = current HEAD (master as it is now, with commits N, O)
--theirs = the revert's target (what master looked like before the merge)
```

This is the OPPOSITE of what you'd expect during a `git merge`:

```
During git merge:
  --ours   = branch you're on
  --theirs = branch you're merging in

During git revert:
  --ours   = current HEAD (the code you have now)
  --theirs = what the revert wants to change it to
```

---

## After Resolving All Conflicts

```bash
# 5. Stage the resolved files
git add src/app.py src/utils.py

# Or stage all resolved files at once
git add .

# 6. Continue the revert
git revert --continue

# 7. Push
git push origin master
```

---

## If You Want to Abort (Cancel the Revert Entirely)

```bash
git revert --abort    # cancels everything, master is back to where it was
```

---

## Useful Commands During Conflict Resolution

```bash
# See all conflicted files
git diff --name-only --diff-filter=U

# See the conflict details for a specific file
git diff src/app.py

# See what the file looked like BEFORE the merge (what revert wants)
git show a1b2c3d^1:src/app.py    # ^1 = parent 1 (master before merge)

# See what the file looks like on current master
git show HEAD:src/app.py

# See what the merge brought in
git show a1b2c3d^2:src/app.py    # ^2 = parent 2 (feature side)

# Use a merge tool (if configured)
git mergetool

# See a 3-way diff (base vs ours vs theirs)
git diff --cc src/app.py
```

---

## Why Conflicts Happen with Revert but Not with Reset

```
git revert:
  - Tries to CREATE A NEW COMMIT that undoes changes
  - Must reconcile with ALL commits that came after the merge
  - If later commits touched the same files/lines → CONFLICT

git reset --hard:
  - Just MOVES THE POINTER back to an older commit
  - Doesn't care about later commits (throws them away)
  - NEVER has conflicts (but destroys history)
```

---

## Alternative: If Conflicts Are Too Complex

If the revert produces too many conflicts to resolve manually,
consider these alternatives:

```bash
# 1. Abort the conflicted revert
git revert --abort

# 2. Use reset instead (if you can force push)
git reset --hard x9y8z7w
git push --force origin master

# 3. Or create a new clean branch (safest)
git checkout -b master-clean x9y8z7w
```

See [revert-master-after-merge.md](revert-master-after-merge.md) for all revert options.

---

## Related

- [revert-master-after-merge.md](revert-master-after-merge.md) — all options to undo a merge
- [git-commit-parents.md](git-commit-parents.md) — understanding ^1 and ^2 parents
- [git-cat-file.md](git-cat-file.md) — inspecting commit internals
