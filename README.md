# Python & FastAPI Learning Reference

A hands-on learning repo with condensed Python and FastAPI examples. Each file covers a topic end-to-end with runnable code, a cheat sheet, and a detailed reference section with beginner-friendly curl examples and arrow diagrams.

**Live Site:** [https://python-fastpy.github.io/learn-fastapi-py/](https://python-fastpy.github.io/learn-fastapi-py/)

---

## Quick Start with uv

[uv](https://docs.astral.sh/uv/) is a fast Python package manager (replaces pip, venv, pyenv). Install it first:

```bash
# Install uv
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Mac/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Set Up a Project

```bash
# Create a new project (creates pyproject.toml + .venv automatically)
uv init my-project
cd my-project

# Or init in current directory
uv init
```

### Install & Run Python

```bash
# Install a specific Python version
uv python install 3.12

# Run a script (uv auto-creates .venv if needed)
uv run python script.py

# Run FastAPI dev server
uv run fastapi dev main.py
```

### Manage Dependencies

```bash
# Add a package (adds to pyproject.toml + installs)
uv add fastapi
uv add uvicorn
uv add pydantic

# Add multiple at once
uv add httpx pytest boto3

# Add dev-only dependency (not needed in production)
uv add --dev pytest ruff mypy

# Remove a package
uv remove httpx

# Sync — install everything from pyproject.toml (like npm install)
uv sync

# See what's installed
uv pip list
```

### How It Works

```
  uv init
    → creates pyproject.toml     (like package.json — lists your dependencies)
    → creates .venv/             (isolated Python environment — like node_modules)
    → creates uv.lock            (exact versions — like package-lock.json)

  uv add fastapi
    → adds "fastapi" to pyproject.toml [dependencies]
    → installs it into .venv/
    → updates uv.lock with exact version

  uv run python app.py
    → runs using .venv Python (no need to activate venv manually)
```

### pyproject.toml (what it looks like)

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "pydantic>=2.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.5.0",
]
```

### uv vs pip Comparison

| Task | pip (old way) | uv (new way) |
|------|--------------|--------------|
| Create venv | `python -m venv .venv` | `uv init` (auto) |
| Activate venv | `.venv\Scripts\activate` | not needed — `uv run` handles it |
| Install package | `pip install fastapi` | `uv add fastapi` |
| Install from file | `pip install -r requirements.txt` | `uv sync` |
| Run script | `python app.py` | `uv run python app.py` |
| Lock versions | `pip freeze > requirements.txt` | automatic (`uv.lock`) |

---

## What's Inside

### FastAPI (`fastapi/`)

| File | Topics |
|------|--------|
| `crud.py` | CRUD operations, Body/Query/Path/Header/Cookie/Form/File params, Depends, Annotated |
| `pydantic.py` | BaseModel, Field validation, validators, nested models, response_model, model_dump |
| `async-await.py` | async/await, gather, create_task, Semaphore, Lock, Event, Queue, shield, httpx |
| `middleware-cors-caching.py` | CORS, GZip, custom middleware, Cache-Control, ETag, rate limiting |
| `routes.py` | APIRouter, response types, error handling, Enum paths, catch-all routes |
| `session.py` | Lifespan, cookie/Redis/JWT sessions, Depends chains, Request/Response |

### Python (`python/`)

| File | Topics |
|------|--------|
| `data-types.py` | Numbers, strings, lists, dicts, sets, tuples, type conversions |
| `functions.py` | Args, kwargs, closures, generators, lambda, decorators |
| `oops.py` | Classes, inheritance, MRO, dunder methods, ABC, dataclasses |
| `decorators.py` | Function/class decorators, chaining, functools.wraps |
| `annotations.py` | Type hints, Optional, Union, TypeVar, Protocol, generics |
| `typeddict.py` | TypedDict, NotRequired, Required, nested, inheritance, JSON patterns |
| `exception-handling.py` | try/except, custom exceptions, context managers, ExceptionGroup |
| `async-await.py` | asyncio, gather, create_task, Semaphore, Lock, Event, Queue, TaskGroup |
| `file-handling.py` | File I/O, CSV, JSON, pathlib, tempfile, shutil |

### Each file has 3 sections:

1. **Content** - Runnable code examples with explanations
2. **Cheat Sheet** - Quick-reference summary of all concepts
3. **Detailed Reference** - Beginner examples with curl commands and arrow diagrams showing data flow

---

## HTML Viewer

An interactive browser-based viewer with:
- Sidebar navigation by folder/file
- Split view: Content on left, Cheat Sheet + Reference on right
- Syntax highlighting, resizable panels
- Search and keyboard shortcuts (`/` to search, `Esc` to clear)

---

## Local Setup

```bash
# Clone the repo
git clone https://github.com/python-fastpy/learn-fastapi-py.git
cd learn-fastapi-py

# Build the viewer data
python viewer/build.py

# Open in browser
# Windows:
start viewer/index.html
# Mac:
open viewer/index.html
# Linux:
xdg-open viewer/index.html
```

After editing any `.py` file, re-run `python viewer/build.py` to update the viewer.

---

## GitHub Pages Deployment

The site auto-deploys on every push to `main` via GitHub Actions.

### One-time setup (if not already done):

1. Go to your repo on GitHub: **Settings > Pages**
2. Under **Source**, select **GitHub Actions**
3. Push to `main` — the workflow runs automatically:
   - Checks out code
   - Runs `python viewer/build.py` to generate `data.js`
   - Deploys the `viewer/` folder to GitHub Pages
4. Site goes live at: `https://python-fastpy.github.io/learn-fastapi-py/`

### Workflow file

The deploy workflow is at [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). It triggers on:
- Every push to `main`
- Manual trigger via **Actions > Deploy to GitHub Pages > Run workflow**

### After deployment

Any changes you push to `main` (new files, updated examples) will automatically rebuild and redeploy the site within ~1-2 minutes.

---

## Project Structure

```
learn-fastapi-py/
├── fastapi/                    # FastAPI learning files
│   ├── crud.py
│   ├── pydantic.py
│   ├── async-await.py
│   ├── middleware-cors-caching.py
│   ├── routes.py
│   ├── session.py
│   └── lifespan.py
├── python/                     # Python learning files
│   ├── data-types.py
│   ├── functions.py
│   ├── oops.py
│   ├── decorators.py
│   ├── annotations.py
│   ├── typeddict.py
│   ├── async-await.py
│   ├── exception-handling.py
│   └── file-handling.py
├── viewer/                     # HTML viewer
│   ├── index.html              # Main viewer page
│   ├── build.py                # Parses .py files → data.js
│   └── data.js                 # Generated (do not edit manually)
├── .github/workflows/
│   └── deploy.yml              # GitHub Pages auto-deploy
├── .gitignore
└── README.md
```
