# CopilotKit — Workflow Diagrams & Local Testing Guide

How a CopilotKit-powered AI assistant works end-to-end, with steps to run it locally.

---

## Standalone Setup (This Repo)

The fastest way to test CopilotKit locally — no Reuters infrastructure needed:

```bash
# Terminal 1: Start the Python backend
cd learn-copilotkit
cp .env.example .env          # Add your OPENAI_API_KEY
uv sync
uv run python 06_full_backend.py   # Starts on :8000

# Terminal 2: Start the React frontend
cd learn-copilotkit/frontend
npm install
npm run dev                   # Starts on :5173

# Open http://localhost:5173 and try each example
```

```
  ┌──────────────┐     ┌──────────────┐
  │  React App   │────▶│  Python      │
  │  (Vite)      │     │  Backend     │
  │  :5173       │     │  (FastAPI)   │
  └──────────────┘     └──────────────┘
```

---

## Part 1: Workflow Diagrams

### High-Level Architecture

```
 ┌──────────────────────────────────────────────────────────────────┐
 │                       Your App (Frontend)                        │
 │                                                                  │
 │  ┌───────────────────┐    ┌────────────────────────────────┐    │
 │  │  Your App Content  │    │  AI Assistant Panel             │    │
 │  │                    │    │                                │    │
 │  │  Page context ─────│────│──▶ CopilotKit                  │    │
 │  │  (story data,      │    │     - Chat UI                  │    │
 │  │   user state, etc) │    │     - Message streaming        │    │
 │  │                    │    │     - Action system             │    │
 │  │                    │    │     - Interrupt handling        │    │
 │  └───────────────────┘    └────────────────────────────────┘    │
 └───────────────────────────────────┬─────────────────────────────┘
                                     │
                                SSE / REST
                                     │
                                     ▼
 ┌───────────────────────────────────────────────────────────────────┐
 │                    Backend (FastAPI + LangGraph)                   │
 │                                                                   │
 │  CopilotKit endpoint  →  LangGraph Agent  →  Tools (@tool)       │
 └───────────────────────────────────────────────────────────────────┘
```

> **USED IN REUTERS:** Production adds MCP skill servers behind the backend:
> ```
> Backend → MCP Protocol → story-drafting :8004, urgent-drafting :8003, text-archive :8000
> ```
> Plus DynamoDB for sessions and checkpoints, and skill-based routing via workflows.

---

### Simple Message Flow (No Tools)

```
 User                    Frontend                    Backend
  │                         │                           │
  │  "What can you          │                           │
  │   help me with?"        │                           │
  │ ───────────────────────▶│                           │
  │                         │  POST /copilotkit         │
  │                         │  { messages: [...] }      │
  │                         │ ─────────────────────────▶│
  │                         │                           │  LLM generates response
  │                         │  SSE: text_delta chunks   │
  │                         │◀──────────────────────────│
  │  Message rendered       │                           │
  │◀────────────────────────│                           │
```

---

### Tool Execution Flow

User asks a question that requires a backend tool.

```
 User              Frontend             Backend
  │                   │                     │
  │  "Search for      │                     │
  │   Apple earnings" │                     │
  │ ──────────────────▶                     │
  │                   │  POST /copilotkit   │
  │                   │ ────────────────────▶
  │                   │                     │  1. LLM analyzes query
  │                   │                     │  2. Selects tool:
  │                   │                     │     search_articles
  │                   │                     │  3. Executes tool
  │                   │                     │  4. LLM formats result
  │                   │  SSE: text deltas   │
  │                   │◀────────────────────│
  │  Results shown    │                     │
  │◀──────────────────│                     │
```

---

### Interrupt Flow (Human-in-the-Loop)

User asks to generate content — backend generates it, interrupts for review, user approves.

```
 User              Frontend             Backend
  │                   │                     │
  │  "Write a draft   │                     │
  │   for AAPL"       │                     │
  │ ──────────────────▶                     │
  │                   │  POST /copilotkit   │
  │                   │ ────────────────────▶
  │                   │                     │  1. LLM generates draft
  │                   │                     │  2. Calls review_draft
  │                   │                     │     action on frontend
  │                   │                     │
  │                   │  SSE: action call   │
  │                   │  review_draft({     │
  │                   │    headline: "...", │
  │                   │    body: "..."      │
  │                   │  })                 │
  │                   │◀────────────────────│
  │                   │                     │
  │  ┌──────────────────────┐               │
  │  │  Draft Review Card    │               │
  │  │  [Approve] [Refine]   │               │
  │  └──────────────────────┘               │
  │                   │                     │
  │  Clicks [Approve] │                     │
  │ ──────────────────▶                     │
  │                   │  resolve("approved")│
  │                   │ ────────────────────▶
  │                   │                     │  3. Continues with
  │                   │                     │     "approved" result
  │                   │  SSE: final text    │
  │                   │◀────────────────────│
  │  Final message    │                     │
  │◀──────────────────│                     │
```

> **USED IN REUTERS:** The interrupt flow is more complex in production:
> - Backend uses LangGraph `interrupt()` to checkpoint state to DynamoDB
> - Interrupt payload includes EventType for rendering the correct UI component
> - Resume loads checkpoint from DynamoDB and continues the graph
> - See: `langgraph_mcp_orchestrator.py` and `reuter-ai-assistant-skills-interrupt.component.tsx`

---

### Refine Loop

What happens when the user clicks "Refine" instead of "Approve":

```
  [Review Card Shown]
          │
          ▼
    User clicks [Refine]
    Types: "Make it shorter"
          │
          ▼
    resolve("refine: Make it shorter")
          │
          ▼
    Backend receives feedback
    Regenerates with instruction
          │
          ▼
    [New Review Card Shown]
    Updated content
          │
          ├── [Approve] ──▶ Done
          └── [Refine]  ──▶ Loop back
```

---

## Part 2: Test Locally

### What You Need Running

```
  ┌──────────────┐     ┌──────────────┐
  │  Frontend    │────▶│  Backend     │
  │  React+Vite  │     │  FastAPI     │
  │  :5173       │     │  :8000       │
  └──────────────┘     └──────────────┘
```

### Step 1: Start the Backend

```bash
cd learn-copilotkit

# Set up environment
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY

# Install and run
uv sync
uv run python 01_hello_copilotkit.py
# Server starts on http://localhost:8000
```

Verify it's running:
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### Step 2: Start the Frontend

```bash
cd learn-copilotkit/frontend

npm install
npm run dev
# Opens at http://localhost:5173
```

### Step 3: Test Each Example

Open http://localhost:5173 and select an example from the sidebar.

| Example | Backend to Run | What to Try |
|---------|---------------|-------------|
| 1. Basic Chat | `01_hello_copilotkit.py` | "Hello, how are you?" |
| 2. Page Context | `03_system_prompt_and_context.py` | Select a story, ask "What story am I editing?" |
| 3. Chat Actions | `06_full_backend.py` | "Make the headline shorter" |
| 4. Interrupts | `06_full_backend.py` | "Write a buzz for Apple earnings" |
| 5. Generative UI | `04_streaming_and_generative_ui.py` | "Search the archive for Apple" |
| 6. Full App | `06_full_backend.py` | All of the above combined |

### Step 4: Test Specific Flows

#### Simple Message (No Tools)
```
Type: "Hello, what can you help me with?"
Expected: AI responds conversationally
```

#### Page Context
```
1. Select example 2 (Page Context)
2. Click the AAPL-EARNINGS story tab
3. Type: "What story am I editing?"
Expected: AI describes the AAPL story using page context
4. Switch to FED-RATES tab
5. Ask again — AI now sees the FED story
```

#### Frontend Action
```
1. Select example 3 (Chat Actions)
2. Type: "Make the headline shorter"
Expected: AI calls update_headline, headline changes in the editor
```

#### Interrupt (Draft Review)
```
1. Select example 4 (Interrupts)
2. Type: "Write a buzz for Apple earnings"
Expected:
  - Review card appears with draft content
  - Three buttons: Approve, Reject, Refine
Test approve: Click Approve → AI confirms
Test refine: Click Refine → Type feedback → New card
```

#### Generative UI
```
1. Select example 5 (Generative UI)
2. Type: "Search the archive for Apple earnings"
Expected: Yellow chip → Blue chip → Green chip with results
```

---

### Debugging Tips

#### Check SSE Stream

Open browser DevTools → Network → filter by "copilotkit" → click the request → look for SSE events.

#### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Network Error" in chat | Backend not running | Start backend on :8000 |
| CORS error | Backend missing CORS middleware | All lesson files include CORS — check the backend is the right file |
| Chat sends but no response | Wrong backend URL | Frontend expects `http://localhost:8000/copilotkit` |
| Actions don't fire | Backend has no tools matching | Use `06_full_backend.py` which has tools for all examples |
| Interrupt card doesn't appear | Using `render` instead of `renderAndWait` | Check the example uses `renderAndWait` for interrupts |

---

### Port Map

| Service | Port | URL |
|---------|------|-----|
| React Frontend (Vite) | 5173 | http://localhost:5173 |
| Python Backend (FastAPI) | 8000 | http://localhost:8000 |

> **USED IN REUTERS:** Production port map is different:
> - LEON Frontend: 3000
> - Backend (FastAPI): 8000
> - DynamoDB Local: 8001
> - Urgent Drafting Skill: 8003
> - Story Drafting Skill: 8004
> - Text Archive Skill: 8005 (or 8000 if standalone)
