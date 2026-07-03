# Python & FastAPI Learning Reference

A hands-on learning repo with condensed Python and FastAPI examples. Each file covers a topic end-to-end with runnable code, a cheat sheet, and a detailed reference section with beginner-friendly curl examples and arrow diagrams.

**Live Site:** [https://python-fastpy.github.io/learn-fastapi-py/](https://python-fastpy.github.io/learn-fastapi-py/)

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
| `exception-handling.py` | try/except, custom exceptions, context managers, ExceptionGroup |
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
