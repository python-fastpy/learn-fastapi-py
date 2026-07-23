# Git Hooks

---

## What are Git Hooks?

Hooks are scripts that git runs automatically before or after
specific events (commit, push, merge, etc.). They enforce rules,
run tests, format code, or prevent bad commits.

```
Workflow with hooks:

You:       git commit -m "add feature"
               |
               v
Hook:      pre-commit script runs
               |
           ┌───┴───┐
           │       │
        passes   fails
           │       │
           v       v
        commit   commit
        created  BLOCKED
           |     (fix and retry)
           v
Hook:   commit-msg script runs
           |
        validates commit message format
           |
           v
        commit finalized
```

---

## Where Hooks Live

```
project/
└── .git/
    └── hooks/
        ├── pre-commit.sample     <-- rename to pre-commit to activate
        ├── commit-msg.sample
        ├── pre-push.sample
        ├── post-merge.sample
        └── ... (other samples)

To activate a hook:
1. Remove .sample extension
2. Make it executable: chmod +x .git/hooks/pre-commit
3. Write your script
```

### Important

```
.git/hooks/ is NOT committed to the repo.
Each developer must set up hooks locally.

Solution: use a tool like Husky (Node.js) or pre-commit (Python)
to share hooks via the repo.
```

---

## Most Common Hooks

### Diagram: Hook Lifecycle

```
git add . → git commit → git push

          ┌──────────┐
          │ git add   │
          └────┬─────┘
               │
          ┌────v─────┐
          │pre-commit │ ← runs BEFORE commit is created
          │ lint,test │   exit 1 = block commit
          └────┬─────┘
               │
          ┌────v──────┐
          │prepare-    │ ← modify default commit message
          │commit-msg  │
          └────┬──────┘
               │
          ┌────v─────┐
          │commit-msg │ ← validate commit message format
          │           │   exit 1 = block commit
          └────┬─────┘
               │
          ┌────v──────┐
          │post-commit│ ← runs AFTER commit (notifications)
          └────┬──────┘
               │
          ┌────v─────┐
          │ pre-push  │ ← runs BEFORE push
          │ full tests│   exit 1 = block push
          └────┬─────┘
               │
          ┌────v──────┐
          │post-merge │ ← runs AFTER merge/pull
          │ npm install│
          └───────────┘
```

---

## pre-commit Hook

Runs before a commit is created. Use for linting, formatting, tests.

### Example: Python — Check for Debug Prints

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Check for print() or debugger statements
if git diff --cached --name-only | xargs grep -l "print(" 2>/dev/null; then
    echo "ERROR: Found print() statements. Remove them before committing."
    exit 1
fi

if git diff --cached --name-only | xargs grep -l "import pdb" 2>/dev/null; then
    echo "ERROR: Found pdb import. Remove debugger before committing."
    exit 1
fi

echo "pre-commit checks passed"
exit 0
```

### Example: Run Linter on Staged Files

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Run flake8 only on staged Python files
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -n "$STAGED_PY" ]; then
    echo "Running flake8 on staged files..."
    flake8 $STAGED_PY
    if [ $? -ne 0 ]; then
        echo "Linting failed. Fix errors before committing."
        exit 1
    fi
fi

exit 0
```

### Example: Run Formatter

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Auto-format staged files with black (Python)
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -n "$STAGED_PY" ]; then
    black $STAGED_PY
    git add $STAGED_PY    # re-stage after formatting
fi

exit 0
```

---

## commit-msg Hook

Validates the commit message format.

### Example: Enforce Conventional Commits

```bash
#!/bin/sh
# .git/hooks/commit-msg

MSG_FILE=$1
MSG=$(cat "$MSG_FILE")

# Pattern: type(scope): description
# Examples: feat(auth): add login page
#           fix(api): handle null response
PATTERN="^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{3,}"

if ! echo "$MSG" | grep -qE "$PATTERN"; then
    echo "ERROR: Invalid commit message format."
    echo ""
    echo "Expected: type(scope): description"
    echo "Types: feat, fix, docs, style, refactor, test, chore"
    echo ""
    echo "Examples:"
    echo "  feat(auth): add login page"
    echo "  fix(api): handle null response"
    echo "  docs: update README"
    echo ""
    echo "Your message: $MSG"
    exit 1
fi

exit 0
```

### Example: Require Ticket Number

```bash
#!/bin/sh
# .git/hooks/commit-msg

MSG=$(cat "$1")

# Require JIRA ticket: ABC-123
if ! echo "$MSG" | grep -qE "^[A-Z]+-[0-9]+"; then
    echo "ERROR: Commit message must start with ticket number (e.g., ABC-123)"
    exit 1
fi

exit 0
```

---

## pre-push Hook

Runs before pushing. Use for running full test suite.

### Example: Run Tests Before Push

```bash
#!/bin/sh
# .git/hooks/pre-push

echo "Running tests before push..."
python -m pytest tests/
if [ $? -ne 0 ]; then
    echo "Tests failed. Push blocked."
    exit 1
fi

echo "All tests passed. Pushing..."
exit 0
```

### Example: Prevent Push to Main

```bash
#!/bin/sh
# .git/hooks/pre-push

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    echo "ERROR: Direct push to $BRANCH is not allowed."
    echo "Create a feature branch and submit a pull request."
    exit 1
fi

exit 0
```

---

## post-merge Hook

Runs after a merge (including `git pull`).

### Example: Auto Install Dependencies

```bash
#!/bin/sh
# .git/hooks/post-merge

# Check if package.json changed
CHANGED=$(git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD)

if echo "$CHANGED" | grep -q "package.json"; then
    echo "package.json changed. Running npm install..."
    npm install
fi

if echo "$CHANGED" | grep -q "requirements.txt"; then
    echo "requirements.txt changed. Running pip install..."
    pip install -r requirements.txt
fi
```

---

## Sharing Hooks with the Team

### Option 1: Husky (Node.js Projects)

```bash
# Install
npm install husky --save-dev
npx husky init

# Creates .husky/ folder (committed to repo)
# Add a pre-commit hook:
echo "npx lint-staged" > .husky/pre-commit
```

```
project/
├── .husky/
│   ├── pre-commit     <-- committed to repo, shared with team
│   └── commit-msg
├── package.json       <-- husky auto-installs hooks on npm install
```

### Option 2: pre-commit Framework (Python Projects)

```bash
# Install
pip install pre-commit

# Create config file
# .pre-commit-config.yaml:
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

# Install hooks
pre-commit install

# Now hooks run on every commit
```

### Option 3: Custom Script in Repo

```bash
# scripts/install-hooks.sh
#!/bin/sh
cp scripts/hooks/* .git/hooks/
chmod +x .git/hooks/*
echo "Hooks installed!"
```

```
project/
├── scripts/
│   ├── install-hooks.sh
│   └── hooks/
│       ├── pre-commit
│       └── commit-msg
```

### Diagram: Shared vs Local Hooks

```
.git/hooks/           <-- LOCAL only, NOT committed
                          Each developer sets up manually

.husky/               <-- COMMITTED to repo
pre-commit-config.yaml    Shared with entire team
scripts/hooks/            Auto-installed via package manager
```

---

## Bypassing Hooks

```bash
# Skip pre-commit and commit-msg hooks
git commit --no-verify -m "emergency fix"
# or
git commit -n -m "emergency fix"

# Skip pre-push hook
git push --no-verify
```

**Use sparingly** — hooks exist for a reason.

---

## Quick Reference

```bash
# Hook location
ls .git/hooks/

# Create a hook
touch .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit    # must be executable

# Test a hook
.git/hooks/pre-commit             # run it directly

# Bypass hooks
git commit --no-verify
git push --no-verify

# Husky (Node.js)
npx husky init
echo "npm test" > .husky/pre-commit

# pre-commit (Python)
pip install pre-commit
pre-commit install
```

---

## All Available Hooks

| Hook               | When it Runs                       | Common Use                    |
|--------------------|------------------------------------|-------------------------------|
| `pre-commit`       | Before commit created              | Lint, format, quick tests     |
| `prepare-commit-msg` | Before editor opens for message | Auto-fill commit template     |
| `commit-msg`       | After message entered              | Validate message format       |
| `post-commit`      | After commit created               | Notifications                 |
| `pre-push`         | Before push                        | Full test suite               |
| `post-merge`       | After merge / pull                 | Install dependencies          |
| `pre-rebase`       | Before rebase                      | Prevent rebase on shared      |
| `post-checkout`    | After checkout / switch            | Rebuild, update submodules    |
| `post-rewrite`     | After rebase / amend               | Update related data           |

---

## Related

- [git-gitignore.md](git-gitignore.md) — hook to check for committed secrets
- [git-branching.md](git-branching.md) — prevent push to protected branches
