# Learn CopilotKit

Build AI chat UIs with CopilotKit + FastAPI + LangGraph. Independently runnable — only needs `OPENAI_API_KEY`.

Each concept links to where it's used in the Reuters AI Assistant codebase via **USED IN REUTERS** references.

---

## Quick Start

```bash
# 1. Backend
cd learn-copilotkit
cp .env.example .env          # Add your OPENAI_API_KEY
uv sync
uv run python 01_hello_copilotkit.py

# 2. Frontend (separate terminal)
cd learn-copilotkit/frontend
npm install
npm run dev

# 3. Open http://localhost:5173
```

---

## Python Lessons (Backend)

| # | File | Teaches | Pairs With |
|---|------|---------|------------|
| 01 | `01_hello_copilotkit.py` | Minimal CopilotKit backend: `create_react_agent` + `add_langgraph_fastapi_endpoint` + CORS | `1-basic-chat.tsx` |
| 02 | `02_backend_with_tools.py` | Agent with `@tool` functions (server-side tools) | — |
| 03 | `03_system_prompt_and_context.py` | System prompts + how `useCopilotReadable` context arrives at the backend | `2-page-context.tsx` |
| 04 | `04_streaming_and_generative_ui.py` | SSE streaming + tool render lifecycle (`inProgress` → `executing` → `complete`) | `5-generative-ui.tsx` |
| 05 | `05_multi_agent.py` | Multiple `LangGraphAGUIAgent` on different paths | — |
| 06 | `06_full_backend.py` | Capstone: system prompt + tools + `CopilotKitMiddleware` + CORS | `3,4,5,6-*.tsx` |

Run any lesson: `uv run python 01_hello_copilotkit.py` (starts on port 8000).

---

## React Examples (Frontend)

| # | File | Demonstrates | Backend |
|---|------|-------------|---------|
| 1 | `frontend/src/examples/1-basic-chat.tsx` | `CopilotKit` provider + `CopilotChat` | 01 or 06 |
| 2 | `frontend/src/examples/2-page-context.tsx` | `useCopilotReadable` — send app data to AI | 03 or 06 |
| 3 | `frontend/src/examples/3-chat-actions.tsx` | `useCopilotAction` — AI calls frontend functions | 06 |
| 4 | `frontend/src/examples/4-interrupts.tsx` | `renderAndWait` — AI pauses for user approval | 06 |
| 5 | `frontend/src/examples/5-generative-ui.tsx` | `render` — live progress UI during tool execution | 04 or 06 |
| 6 | `frontend/src/examples/6-full-app.tsx` | All patterns combined: story editor + chat | 06 |

Open http://localhost:5173 and select an example from the sidebar.

---

## Backend + Frontend Pairing Guide

Most frontend examples need the **full backend** (`06_full_backend.py`) because they use chat actions, interrupts, or generative UI features. Start there if unsure.

For learning concepts in isolation:

```
Example 1 (Basic Chat)     →  01_hello_copilotkit.py   (simplest possible)
Example 2 (Page Context)   →  03_system_prompt_and_context.py
Example 5 (Generative UI)  →  04_streaming_and_generative_ui.py
Everything else             →  06_full_backend.py
```

---

## Reference Docs

| Doc | Contents |
|-----|----------|
| [How CopilotKit Works](docs/how-copilotkit-works.md) | Architecture, three-layer stack, key concepts (actions, interrupts, generative UI, context) |
| [React Examples Reference](docs/copilotkit-react-examples.md) | 10 code examples with explanations and Reuters mappings |
| [Workflow & Local Testing](docs/copilotkit-workflow-and-local-testing.md) | End-to-end workflow diagrams + local testing guide |

---

## Key Concepts

| Concept | CopilotKit API | What It Does |
|---------|---------------|--------------|
| Page context | `useCopilotReadable` | Send app data to the AI (e.g., current story) |
| Frontend tools | `useCopilotAction` + `handler` | AI calls functions in the browser |
| Interrupts | `useCopilotAction` + `renderAndWait` | AI pauses for user approval/input |
| Generative UI | `useCopilotAction` + `render` | Show progress UI during tool execution |
| Backend tools | `@tool` decorator | Server-side functions the AI can call |
| Multi-agent | Multiple `LangGraphAGUIAgent` | Different agents on different API paths |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- OpenAI API key
