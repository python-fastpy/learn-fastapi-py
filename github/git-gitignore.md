# Git .gitignore

---

## What is .gitignore?

A `.gitignore` file tells git which files/folders to ignore — they
won't show up in `git status` and won't be tracked.

```
Project/
├── .gitignore          <-- rules go here
├── src/
│   └── app.py          <-- tracked
├── node_modules/       <-- ignored (in .gitignore)
├── .env                <-- ignored (secrets)
├── build/              <-- ignored (generated)
└── debug.log           <-- ignored (temp file)
```

---

## Pattern Syntax

```bash
# ---- BASIC PATTERNS ----

# Ignore a specific file
debug.log

# Ignore all files with an extension
*.log
*.pyc
*.class

# Ignore a specific folder (and everything inside)
node_modules/
__pycache__/
.venv/

# Ignore a file in a specific path
/config/local.yml       # only in root config/
config/local.yml        # in any config/ folder

# ---- NEGATION (!) ----

# Ignore all .log files EXCEPT important.log
*.log
!important.log

# ---- WILDCARDS ----

# * = matches anything except /
*.txt                   # all .txt files
doc/*.pdf               # .pdf files in doc/ only

# ** = matches any directory depth
**/logs                 # logs folder anywhere
**/logs/*.log           # .log files in any logs/ folder
src/**/*.test.js        # .test.js files anywhere under src/

# ? = matches single character
file?.txt               # file1.txt, fileA.txt, but not file10.txt

# [] = matches character set
file[0-9].txt           # file0.txt through file9.txt
file[abc].txt           # filea.txt, fileb.txt, filec.txt

# ---- COMMENTS ----

# This is a comment (lines starting with #)
# Blank lines are ignored
```

### Pattern Diagram

```
Pattern:        What it matches:
--------        ----------------
*.log           error.log, debug.log, app.log
                src/error.log, any/path/debug.log

/debug.log      ONLY debug.log in root directory
                NOT src/debug.log

debug.log       debug.log in ANY directory
                src/debug.log, a/b/debug.log

logs/           logs/ folder at any depth
                src/logs/, a/b/logs/

/logs/          ONLY logs/ in root directory

**/logs/        logs/ folder at any depth (same as logs/)

src/**/*.js     src/app.js, src/utils/helper.js, src/a/b/c.js
```

---

## Common .gitignore Templates

### Python

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/
*.egg
.venv/
env/
venv/
.env
*.log
.mypy_cache/
.pytest_cache/
.coverage
htmlcov/
```

### Node.js

```
node_modules/
npm-debug.log*
.env
.env.local
dist/
build/
coverage/
*.tgz
.DS_Store
```

### Java

```
*.class
*.jar
*.war
*.ear
target/
build/
.gradle/
.idea/
*.iml
out/
```

### General (Add to Any Project)

```
# OS files
.DS_Store
Thumbs.db
Desktop.ini

# Editor files
.idea/
.vscode/
*.swp
*.swo
*~

# Environment / secrets
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Build output
dist/
build/
out/
```

---

## Global .gitignore (Applied to ALL Repos)

```bash
# Create a global .gitignore
git config --global core.excludesFile ~/.gitignore_global

# Add common ignores to it
# ~/.gitignore_global:
.DS_Store
Thumbs.db
.idea/
.vscode/
*.swp
```

### Diagram: Global vs Local

```
~/.gitignore_global        <-- applies to ALL repos on your machine
                                (OS files, editor files)

project/.gitignore         <-- applies to THIS repo only
                                (node_modules, .env, build/)

project/src/.gitignore     <-- applies to src/ and subdirectories
                                (can override parent rules)
```

---

## Ignore Already Tracked Files

**Problem:** You added a file to `.gitignore` but git still tracks it
because it was committed before.

```bash
# Step 1: Add to .gitignore
echo ".env" >> .gitignore

# Step 2: Remove from git tracking (but keep the file on disk)
git rm --cached .env

# Step 3: Commit
git add .gitignore
git commit -m "stop tracking .env"

# For a folder:
git rm -r --cached node_modules/
```

### Diagram: Why .gitignore Doesn't Work on Tracked Files

```
BEFORE:
.env is tracked (committed previously)
.gitignore has: .env

git status still shows .env changes!  <-- .gitignore only ignores UNTRACKED files

FIX:
git rm --cached .env    <-- removes from tracking, keeps file on disk

AFTER:
.env is untracked
.gitignore ignores it
git status: clean
```

### Remove ALL Tracked Files That Should Be Ignored

```bash
# Nuclear option: remove all files from tracking, re-add with .gitignore applied
git rm -r --cached .
git add .
git commit -m "apply .gitignore to all files"

# WARNING: this re-adds everything, so make sure .gitignore is correct first
```

---

## Debugging .gitignore

```bash
# Check if a file is ignored and WHY
git check-ignore -v file.py
# output: .gitignore:3:*.py    file.py
#          ^           ^        ^
#          which file  pattern  the file being checked

# Check if a file is ignored (simple yes/no)
git check-ignore file.py
# output: file.py     (means yes, it's ignored)
# no output = not ignored

# List all ignored files
git status --ignored

# List all ignored files (short format)
git status --ignored --short
```

---

## .gitignore Precedence

```
Rules are checked in this order (later overrides earlier):

1. Patterns in .gitignore in the same directory
2. Patterns in .gitignore in parent directories (up to repo root)
3. Patterns in .git/info/exclude (local, not committed)
4. Patterns in core.excludesFile (global ~/.gitignore_global)

Within a file, later rules override earlier:
  *.log          <-- ignore all .log
  !important.log <-- but NOT important.log (overrides above)
```

---

## .git/info/exclude (Personal Ignores)

For files only YOU want to ignore (not shared with the team):

```bash
# Edit .git/info/exclude (not committed, not in .gitignore)
# Same syntax as .gitignore

# Example: you use a specific editor that creates temp files
*.sublime-workspace
my-local-notes.txt
```

### Diagram: Where to Put Ignore Rules

```
Want to share with team?
│
├── YES --> .gitignore (committed to repo)
│
└── NO (personal only)
    │
    ├── For this repo only --> .git/info/exclude
    │
    └── For ALL repos --> ~/.gitignore_global
```

---

## Quick Reference

```bash
# Check why a file is/isn't ignored
git check-ignore -v file.py

# Stop tracking a file (keep on disk)
git rm --cached file.py
git rm -r --cached folder/

# List ignored files
git status --ignored

# Force add an ignored file (override .gitignore)
git add -f ignored-file.py

# Global gitignore
git config --global core.excludesFile ~/.gitignore_global
```

---

## Related

- [git-hooks.md](git-hooks.md) — pre-commit hooks to enforce .gitignore
