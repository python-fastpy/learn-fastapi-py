# Git Bisect

---

## What is Bisect?

`git bisect` uses binary search to find which commit introduced a bug.
Instead of checking every commit, it cuts the search space in half each time.

```
100 commits to search:

Linear search:  check 1, 2, 3, 4, ... up to 100 (worst case: 100 checks)

Binary search:  check 50 → bad
                check 25 → good
                check 37 → bad
                check 31 → good
                check 34 → bad
                check 33 → good
                commit 34 introduced the bug!  (only 6 checks!)
```

---

## How It Works (Visual)

```
Commits:  A---B---C---D---E---F---G---H---I---J
          ^                                   ^
         GOOD                                BAD
         (no bug)                         (has bug)

Step 1: git bisect picks the middle → E
        A---B---C---D---[E]---F---G---H---I---J
                         ^
                     is this good or bad?

You test: E is GOOD

Step 2: bug is between E and J, picks middle → G
        A---B---C---D---E---F---[G]---H---I---J
                                 ^
                             is this good or bad?

You test: G is BAD

Step 3: bug is between E and G, picks middle → F
        A---B---C---D---E---[F]---G---H---I---J
                             ^
                         is this good or bad?

You test: F is GOOD

RESULT: F is good, G is bad → commit G introduced the bug!
```

---

## Basic Usage

```bash
# 1. Start bisect
git bisect start

# 2. Mark current commit as BAD (has the bug)
git bisect bad

# 3. Mark a known GOOD commit (didn't have the bug)
git bisect good a1b2c3d

# Git now checks out the middle commit and tells you:
# Bisecting: 5 revisions left to test after this (roughly 3 steps)

# 4. Test if the bug exists at this commit
#    Run your tests, check the feature, etc.

# 5. Tell git the result
git bisect good    # no bug here
# or
git bisect bad     # bug exists here

# 6. Repeat steps 4-5 until git finds the commit:
# a1b2c3d is the first bad commit
# commit a1b2c3d
# Author: ...
# Date: ...
#     broke the login page

# 7. When done, go back to where you started
git bisect reset
```

---

## Step-by-Step Example

```bash
# Scenario: login page broke sometime in the last 20 commits

# Start
git bisect start

# Current commit (HEAD) has the bug
git bisect bad

# 20 commits ago it worked fine
git bisect good HEAD~20
# Bisecting: 10 revisions left to test after this (roughly 3 steps)
# [f1e2d3c] refactor auth module     <-- git checked out this commit

# Test: does login work? YES
git bisect good
# Bisecting: 5 revisions left to test
# [a1b2c3d] add new validation       <-- checked out next

# Test: does login work? NO
git bisect bad
# Bisecting: 2 revisions left
# [x9y8z7w] update config            <-- checked out next

# Test: does login work? YES
git bisect good
# Bisecting: 0 revisions left
# [b2c3d4e] change password hashing  <-- checked out next

# Test: does login work? NO
git bisect bad
# b2c3d4e is the first bad commit
# Author: John Doe
# Date: Mon Jul 20
#     change password hashing        <-- THIS commit broke login!

# Done — go back to original branch
git bisect reset
```

---

## Automated Bisect (With a Script)

Instead of manually testing, give bisect a script that returns:
- Exit code 0 = GOOD
- Exit code 1 = BAD

```bash
# Automated bisect with a test command
git bisect start
git bisect bad HEAD
git bisect good HEAD~50

# Run a script at each step automatically
git bisect run python -m pytest tests/test_login.py

# Or with a custom script
git bisect run ./test-login.sh

# Or with any command
git bisect run make test
```

### Diagram: Manual vs Automated

```
MANUAL:
You:  start → bad → good → [test] → good → [test] → bad → ... → found!
               human tests each commit

AUTOMATED:
You:  start → bad → good → run script
Git:  [test] → good → [test] → bad → [test] → good → ... → found!
               script tests each commit automatically
```

### Example Test Script

```bash
#!/bin/bash
# test-login.sh

# Build the project
npm run build 2>/dev/null

# Run specific test
npm test -- --grep "login" 2>/dev/null

# Exit code 0 = good, non-zero = bad
# npm test already returns the right exit codes
```

---

## Bisect with Terms (Custom Labels)

Instead of "good" and "bad", use custom terms:

```bash
# Use "old" and "new" instead of "good" and "bad"
git bisect start --term-old=working --term-new=broken

git bisect broken        # current is broken
git bisect working HEAD~20   # this was working

# Then use your terms:
git bisect working       # this commit works
git bisect broken        # this commit is broken
```

---

## Skipping Commits

If you can't test a particular commit (doesn't build, etc.):

```bash
git bisect skip
# Git will try another nearby commit

# Skip a range of commits
git bisect skip v2.1..v2.5
```

### Diagram: Skip

```
Commits:  A---B---C---D---E---F---G---H---I---J
                       ^
                  D doesn't compile, can't test

git bisect skip    <-- git picks C or E instead
```

---

## View Bisect Log and Replay

```bash
# See the bisect log (all good/bad decisions)
git bisect log
# git bisect start
# git bisect bad HEAD
# git bisect good a1b2c3d
# git bisect good f1e2d3c
# git bisect bad x9y8z7w

# Save bisect log to file
git bisect log > bisect.log

# Replay a saved bisect session
git bisect replay bisect.log
```

---

## Visualize Bisect Progress

```bash
# Show remaining suspects
git bisect visualize
# Opens gitk (or log) showing remaining commits to check

# Text-based visualization
git bisect visualize --oneline
```

---

## Common Patterns

### Find When a Test Started Failing

```bash
git bisect start
git bisect bad HEAD
git bisect good v1.0       # last known working version
git bisect run python -m pytest tests/test_feature.py -x
# -x = stop on first failure
```

### Find When a Performance Regression Happened

```bash
#!/bin/bash
# perf-test.sh
result=$(python benchmark.py)
if [ "$result" -gt 500 ]; then
    exit 1    # BAD: takes more than 500ms
else
    exit 0    # GOOD: under 500ms
fi
```

```bash
git bisect start
git bisect bad HEAD
git bisect good HEAD~100
git bisect run ./perf-test.sh
```

### Find When a File Was Deleted

```bash
git bisect start
git bisect bad HEAD              # file is missing now
git bisect good HEAD~50          # file existed here
git bisect run test -f src/important.py   # test if file exists
```

---

## Quick Reference

```bash
# Manual bisect
git bisect start
git bisect bad                   # current has bug
git bisect good a1b2c3d          # this commit was ok
git bisect good                  # current test = ok
git bisect bad                   # current test = has bug
git bisect reset                 # done, go back

# Automated bisect
git bisect start
git bisect bad HEAD
git bisect good HEAD~50
git bisect run ./test.sh         # script: exit 0=good, 1=bad

# Other
git bisect skip                  # can't test this commit
git bisect log                   # show decisions so far
git bisect visualize             # show remaining suspects
git bisect replay file.log       # replay saved session
```

---

## Related

- [git-reset-vs-revert.md](git-reset-vs-revert.md) — fixing the bug once found
- [git-branching.md](git-branching.md) — bisect works across branches
