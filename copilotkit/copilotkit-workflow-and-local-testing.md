# CopilotKit — Workflow Diagram & Local Testing Guide

How the CopilotKit-powered Reuters AI Assistant works end-to-end, with steps to run it locally.

---

## Part 1: Workflow Diagrams

### High-Level Architecture

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                          LEON (Editorial Platform)                       │
 │                                                                          │
 │  ┌─────────────────────┐    ┌──────────────────────────────────────┐    │
 │  │   Story Editor       │    │   AI Assistant Panel                  │    │
 │  │                      │    │                                      │    │
 │  │  - headline          │    │  ┌──────────────────────────────┐   │    │
 │  │  - body              │───▶│  │  ReutersAssistantAI          │   │    │
 │  │  - slug              │    │  │  (@reuters/assistant-v2)      │   │    │
 │  │  - RIC               │    │  │                              │   │    │
 │  │  - language           │    │  │  ┌────────────────────────┐ │   │    │
 │  │                      │    │  │  │  CopilotKit (core)      │ │   │    │
 │  │  Page Context ───────│────│──│──│  - Chat UI              │ │   │    │
 │  │                      │    │  │  │  - Message streaming    │ │   │    │
 │  └─────────────────────┘    │  │  │  - Action system        │ │   │    │
 │                              │  │  │  - Interrupt handling   │ │   │    │
 │                              │  │  └────────────────────────┘ │   │    │
 │                              │  └──────────────────────────────┘   │    │
 │                              └──────────────────────────────────────┘    │
 └───────────────────────────────────────┬──────────────────────────────────┘
                                         │
                                    SSE / GraphQL
                                         │
                                         ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                        Backend (FastAPI + LangGraph)                      │
 │                                                                          │
 │  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
 │  │ copilotkit_rest  │  │  LangGraph MCP    │  │  Session Manager      │  │
 │  │ (request parser) │─▶│  Orchestrator     │  │  (DynamoDB)           │  │
 │  └─────────────────┘  │                    │  └───────────────────────┘  │
 │                        │  - Query analysis  │                            │
 │                        │  - Tool selection  │  ┌───────────────────────┐  │
 │                        │  - Fast-path match │  │  Checkpoint Store     │  │
 │                        │  - interrupt()     │  │  (DynamoDB)           │  │
 │                        └────────┬───────────┘  └───────────────────────┘  │
 └─────────────────────────────────┼────────────────────────────────────────┘
                                   │
                              MCP Protocol
                     ┌─────────────┼─────────────┐
                     │             │             │
                     ▼             ▼             ▼
              ┌────────────┐ ┌──────────┐ ┌──────────────┐
              │ story-     │ │ urgent-  │ │ text-        │
              │ drafting   │ │ drafting │ │ archive      │
              │ :8004      │ │ :8003    │ │ :8000        │
              │            │ │          │ │              │
              │ - spot     │ │ - urgent │ │ - search     │
              │ - buzz     │ │ - regen  │ │   reuters    │
              │ - bulletin │ │          │ │   archive    │
              │ - update   │ │          │ │              │
              └────────────┘ └──────────┘ └──────────────┘
                    MCP Skills (FastMCP on ECS Fargate)
```

---

### Simple Message Flow (No Interrupt)

A user asks a question the AI can answer without tools.

```
 User                    Frontend                    Backend
  │                         │                           │
  │  "What story am I       │                           │
  │   editing?"             │                           │
  │ ───────────────────────▶│                           │
  │                         │                           │
  │                         │  POST /copilotkit         │
  │                         │  {                        │
  │                         │    messages: [...],       │
  │                         │    properties: {          │
  │                         │      externalContext: {   │
  │                         │        headline: "...",   │
  │                         │        ric: "AAPL.O"     │
  │                         │      }                   │
  │                         │    }                     │
  │                         │  }                       │
  │                         │ ─────────────────────────▶│
  │                         │                           │
  │                         │                           │  LLM sees page context
  │                         │                           │  No tools needed
  │                         │                           │
  │                         │  SSE: text_delta chunks   │
  │                         │  "You're editing the      │
  │                         │   Apple earnings story    │
  │                         │   (AAPL.O)..."            │
  │                         │◀──────────────────────────│
  │                         │                           │
  │  Message rendered       │                           │
  │  in chat panel          │                           │
  │◀────────────────────────│                           │
  │                         │                           │
```

---

### Tool Execution Flow (No Interrupt)

User asks for a text archive search — backend calls MCP tool, streams result.

```
 User              Frontend             Backend              text-archive
  │                   │                     │                  MCP :8000
  │  "Search for      │                     │                     │
  │   AAPL earnings"  │                     │                     │
  │ ──────────────────▶                     │                     │
  │                   │  POST /copilotkit   │                     │
  │                   │ ────────────────────▶                     │
  │                   │                     │                     │
  │                   │                     │  1. LLM analyzes    │
  │                   │                     │     query           │
  │                   │                     │                     │
  │                   │                     │  2. Selects tool:   │
  │                   │                     │     search_reuters  │
  │                   │                     │     _text_archive   │
  │                   │                     │                     │
  │                   │                     │  MCP tool call      │
  │                   │                     │ ────────────────────▶
  │                   │                     │                     │
  │                   │                     │                     │ Calls Reuters
  │                   │                     │                     │ Text Archive API
  │                   │                     │                     │ (OAuth + polling)
  │                   │                     │                     │
  │                   │                     │  Tool result        │
  │                   │                     │◀────────────────────│
  │                   │                     │                     │
  │                   │                     │  3. LLM formats     │
  │                   │                     │     response with   │
  │                   │                     │     search results  │
  │                   │                     │                     │
  │                   │  SSE: text deltas   │                     │
  │                   │  + MCP metadata     │                     │
  │                   │◀────────────────────│                     │
  │                   │                     │                     │
  │  Shows:           │                     │                     │
  │  - MCP badge      │                     │                     │
  │  - Skill chip     │                     │                     │
  │  - Search results │                     │                     │
  │◀──────────────────│                     │                     │
```

---

### Interrupt Flow (Human-in-the-Loop)

User asks to draft a buzz — backend generates it, interrupts for review, user approves.

```
 User              Frontend             Backend              story-drafting
  │                   │                     │                  MCP :8004
  │  "Write a news    │                     │                     │
  │   buzz for AAPL"  │                     │                     │
  │ ──────────────────▶                     │                     │
  │                   │  POST /copilotkit   │                     │
  │                   │ ────────────────────▶                     │
  │                   │                     │                     │
  │                   │                     │  1. Workflow        │
  │                   │                     │     selected:       │
  │                   │                     │     news-buzz-      │
  │                   │                     │     drafting        │
  │                   │                     │                     │
  │                   │                     │  2. RIC resolution  │
  │                   │                     │ ────────────────────▶
  │                   │                     │  validate_ric       │
  │                   │                     │◀────────────────────│
  │                   │                     │                     │
  │                   │                     │  3. Fetch headlines  │
  │                   │                     │ ────────────────────▶
  │                   │                     │  fetch_headlines     │
  │                   │                     │◀────────────────────│
  │                   │                     │                     │
  │                   │                     │  4. Generate buzz    │
  │                   │                     │ ────────────────────▶
  │                   │                     │  generate_news_buzz  │
  │                   │                     │◀────────────────────│
  │                   │                     │                     │
  │                   │                     │  5. interrupt()      │
  │                   │                     │     Checkpoint ──▶ DynamoDB
  │                   │                     │                     │
  │                   │  SSE: interrupt     │                     │
  │                   │  {                  │                     │
  │                   │    type: "NEWS_BUZZ │                     │
  │                   │          .REVIEW",  │                     │
  │                   │    content: "...",  │                     │
  │                   │    actions: [       │                     │
  │                   │      "approve",     │                     │
  │                   │      "refine"       │                     │
  │                   │    ]                │                     │
  │                   │  }                  │                     │
  │                   │◀────────────────────│                     │
  │                   │                     │                     │
  │  ┌──────────────────────┐               │                     │
  │  │  Buzz Review Card     │               │                     │
  │  │                       │               │                     │
  │  │  AAPL.O — Apple Inc   │               │                     │
  │  │                       │               │                     │
  │  │  "Apple shares rose   │               │                     │
  │  │   3.2% after..."      │               │                     │
  │  │                       │               │                     │
  │  │  [Approve] [Refine]   │               │                     │
  │  └──────────────────────┘               │                     │
  │                   │                     │                     │
  │                   │                     │                     │
  │  Clicks           │                     │                     │
  │  [Approve]        │                     │                     │
  │ ──────────────────▶                     │                     │
  │                   │                     │                     │
  │                   │  resolve("approved")│                     │
  │                   │  POST /copilotkit   │                     │
  │                   │  + interrupt_       │                     │
  │                   │    resolution       │                     │
  │                   │ ────────────────────▶                     │
  │                   │                     │                     │
  │                   │                     │  6. Resume from     │
  │                   │                     │     DynamoDB        │
  │                   │                     │     checkpoint      │
  │                   │                     │                     │
  │                   │                     │  7. Continue        │
  │                   │                     │     execution       │
  │                   │                     │                     │
  │                   │  SSE: final text    │                     │
  │                   │  "Here's your       │                     │
  │                   │   approved buzz..." │                     │
  │                   │◀────────────────────│                     │
  │                   │                     │                     │
  │  Final message    │                     │                     │
  │  rendered         │                     │                     │
  │◀──────────────────│                     │                     │
```

---

### Refine Loop (User Asks for Changes)

What happens when the user clicks "Refine" instead of "Approve":

```
  [Interrupt Card Shown]
          │
          ▼
    User clicks [Refine]
    Types: "Make it shorter"
          │
          ▼
    resolve("refine: Make it shorter")
          │
          ▼
    Backend resumes from checkpoint
    with refinement instruction
          │
          ▼
    Calls generate_news_buzz again
    with original context + feedback
          │
          ▼
    interrupt() again
    New checkpoint ──▶ DynamoDB
          │
          ▼
    [New Interrupt Card Shown]
    Updated buzz content
          │
          ├── [Approve] ──▶ Done, final message sent
          │
          └── [Refine]  ──▶ Loop back to top
                             (can refine multiple times)
```

---

### Fast-Path vs Normal Flow

The backend has two routing paths depending on whether context is sufficient:

```
                        User Message
                             │
                             ▼
                    ┌─────────────────┐
                    │  Fast-Path      │
                    │  Pattern Match  │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              Pattern matches?   No match
              + All params         │
              available from       │
              page context         │
                    │               │
                    ▼               ▼
             ┌──────────┐   ┌──────────────┐
             │ FAST PATH │   │ NORMAL PATH  │
             │ ~100ms    │   │ ~2-3 seconds │
             │           │   │              │
             │ Skip LLM  │   │ LLM analyzes │
             │ query     │   │ query, picks │
             │ analysis  │   │ tools        │
             │           │   │              │
             │ Direct    │   │ May need     │
             │ tool call │   │ multiple     │
             │           │   │ tool calls   │
             └──────────┘   └──────────────┘
                    │               │
                    └───────┬───────┘
                            ▼
                     Response streamed
                     back to user

  Fast-path examples:
    "Draft an Urgent for USN123456"
      → regex matches, USN extracted, calls generate_urgent directly

    "Search for AAPL earnings in the archive"
      → regex matches, query extracted, calls search_reuters_text_archive

  Normal-path examples:
    "Can you help me rewrite this story?"
      → No pattern match, LLM decides which workflow/tool to use
```

---

### Session & State Management

```
  ┌──────────────────────────────────────────────────────────┐
  │                      DynamoDB Tables                      │
  │                                                          │
  │  ┌────────────────┐  ┌──────────────────────────────┐   │
  │  │ session-history │  │ langgraph-checkpoints        │   │
  │  │                 │  │                              │   │
  │  │ PK: tenant_id   │  │ PK: thread_id               │   │
  │  │ SK: session_id   │  │ SK: checkpoint_id           │   │
  │  │                 │  │                              │   │
  │  │ - messages[]    │  │ - graph state snapshot       │   │
  │  │ - title         │  │ - pending tool calls        │   │
  │  │ - created_at    │  │ - interrupt metadata        │   │
  │  │ - updated_at    │  │ - LLM conversation so far   │   │
  │  │ - metadata      │  │                              │   │
  │  │ - TTL (30 days) │  │ Used for:                    │   │
  │  │                 │  │ - Resuming after interrupt   │   │
  │  │ Used for:       │  │ - Multi-turn tool chains    │   │
  │  │ - Chat history  │  │ - Crash recovery            │   │
  │  │ - Session list  │  │                              │   │
  │  │ - Replay        │  │                              │   │
  │  └────────────────┘  └──────────────────────────────┘   │
  │                                                          │
  │  ┌────────────────┐  ┌──────────────────────────────┐   │
  │  │ skills-registry │  │ tenant-registry              │   │
  │  │                 │  │                              │   │
  │  │ - MCP server    │  │ - tenant config              │   │
  │  │   URLs          │  │ - skill access control       │   │
  │  │ - cached tool   │  │   (READ/WRITE/ADMIN)         │   │
  │  │   schemas       │  │                              │   │
  │  └────────────────┘  └──────────────────────────────┘   │
  └──────────────────────────────────────────────────────────┘

  Session lifecycle:
    1. User opens assistant → frontend generates session ID (UUID)
    2. Stored in localStorage for cross-reload persistence
    3. First message creates session in DynamoDB
    4. Each message appends to session's messages[]
    5. Session title auto-generated from first user message
    6. TTL expires after 30 days of inactivity
```

---

## Part 2: Test Locally — Step by Step

### What You Need Running

To test the full CopilotKit flow locally, you need three things:

```
  ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Frontend    │────▶│  Backend     │────▶│  MCP Skill   │
  │  LEON        │     │  FastAPI     │     │  (optional)  │
  │  :3000       │     │  :8000       │     │  :8003/8004  │
  └─────────────┘     └──────────────┘     └──────────────┘
```

You can test in stages — start simple and add layers.

---

### Stage 1: Backend Only (Quickest)

Test the backend health and basic API without any frontend.

```bash
# Terminal 1 — Start the backend
cd reuters-ai_assistant/reuters-assistant_backend

# Copy env template and fill in required values
cp .env.example .env
# Edit .env — at minimum you need:
#   OPENAI_API_KEY=sk-...
#   AWS_REGION=eu-west-1
#   ENVIRONMENT=local

# Start with Docker (recommended)
./run-docker-local.sh

# OR start directly with uv
uv sync
uv run uvicorn src.app:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

```bash
# Terminal 2 — Verify it's running
curl http://localhost:8000/health
# Expected: {"status": "healthy", ...}

# Check CopilotKit endpoint
curl http://localhost:8000/api/copilotkit/health
# Expected: {"status": "ok"}

# Check registered skills
curl http://localhost:8000/api/v1/admin/skills \
  -H "Authorization: Bearer YOUR_JWT"
```

---

### Stage 2: Backend + MCP Skill

Add a skill server so the backend can actually call tools.

```bash
# Terminal 1 — Backend (already running from Stage 1)

# Terminal 2 — Start a skill server (e.g., story-drafting)
cd sphinx_leon-assistant-skills/story-drafting

# Copy env and configure
cp .env.example .env
# Edit .env — needs:
#   OPENAI_API_KEY=sk-...
#   GEMINI_API_KEY=...  (for buzz generation)
#   SPHINX_AUTH_URL=...
#   RMA_API_KEY=...     (for RIC validation)

# Install and run
uv sync
uv run python run.py
# Starts on http://localhost:8004

# Terminal 3 — Verify skill health
curl http://localhost:8004/health
# Expected: {"status": "healthy"}

# List available tools
curl http://localhost:8004/mcp/tools
```

**Register the skill with the backend:**

```bash
# Tell the backend about the local skill server
curl -X POST http://localhost:8000/api/v1/admin/skills \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "story-drafting",
    "url": "http://localhost:8004",
    "transport": "streamable_http"
  }'
```

---

### Stage 3: Frontend + Backend (Full Stack)

Run LEON's frontend pointing at the local backend.

```bash
# Terminal 1 — Backend (already running)
# Terminal 2 — Skill server (already running, optional)

# Terminal 3 — Frontend
cd lynx_leon

# Install dependencies (requires JFrog token for @reuters packages)
export JFROG_TOKEN=your-jfrog-token
pnpm install

# The environment config in src/config/environment.ts maps
# 'local' environment to http://localhost:8000 backend URLs.
#
# Make sure the AI assistant component uses environment="local":
# (check reuter-ai-assistant-v2.component.tsx)

# Start dev server
pnpm start
# Opens at http://localhost:3000
```

**Navigate to a story page in LEON and open the AI Assistant panel.**

---

### Stage 4: Test Specific Flows

Once everything is running, test these flows:

#### Simple Message (No Tools)

```
Type: "Hello, what can you help me with?"
Expected: AI responds with capabilities list
Verify: No MCP badges or skill chips appear (pure LLM response)
```

#### Page Context

```
1. Open a story in LEON (e.g., an AAPL earnings story)
2. Type: "What story am I looking at?"
Expected: AI describes the story using page context data
Verify: Console shows page context being sent in request
```

#### Tool Call (Text Archive)

```
Type: "Search for Apple earnings in the archive"
Expected:
  1. Skill chip appears: "search_reuters_text_archive" (running)
  2. MCP badge shows "text-archive" server
  3. Results displayed in chat
  4. Skill chip updates to completed
```

#### Interrupt (Buzz Review)

```
Type: "Write a news buzz for AAPL"
Expected:
  1. Multiple skill chips appear (validate_ric, fetch_headlines, generate_news_buzz)
  2. Review card appears with the generated buzz
  3. Three buttons: Approve, Refine, Reject
Test approve: Click "Approve" → Final message with approved buzz
Test refine:  Click "Refine" → Type feedback → New review card appears
Test reject:  Click "Reject" → AI acknowledges and stops
```

#### Auto-Message (Urgent Drafting)

```
1. Open a story with version type "NEWSBREAK" in LEON
2. The AI assistant should auto-open and send: "Draft an Urgent for {USN}"
3. Expected: Urgent drafting workflow starts automatically
Verify: Check the auto-message useEffect logs in console (RAIA::AUTO_MESSAGE::*)
```

---

### Debugging Tips

#### Check SSE Stream

Open browser DevTools → Network → filter by "copilotkit" → click the SSE request → EventStream tab:

```
data: {"data":{"generateCopilotResponse":{...}}, "hasNext": true}    ← Initial
data: {"incremental":[{"items":["Hello"]}], "hasNext": true}         ← Text chunk
data: {"incremental":[{"items":[" world"]}], "hasNext": true}        ← Text chunk
data: {"hasNext": false}                                              ← Done
```

#### Check Backend Logs

```bash
# If running with Docker:
docker logs -f reuters-assistant-backend

# Key log lines to look for:
#   "Processing message for session ..."
#   "Selected tools: [...]"
#   "Executing MCP tool: ..."
#   "Interrupt triggered: ..."
#   "Resuming from checkpoint: ..."
```

#### Check Skill Server Logs

```bash
# Look for tool invocations:
#   "Tool called: generate_news_buzz"
#   "RIC validation: AAPL.O → valid"
#   "LLM call: gemini-2-5-pro → 200"
```

#### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Network Error" in chat | Backend not running | Start backend on :8000 |
| "401 Unauthorized" | Missing/expired JWT | Get fresh token from LEON auth |
| No skill chips appear | Skill not registered | Register skill via admin API |
| Interrupt card doesn't show | Frontend event type mismatch | Check `EventType` mapping in skills-interrupt component |
| "Checkpoint not found" | DynamoDB not configured for local | Set `DYNAMODB_ENDPOINT=http://localhost:8001` + run DynamoDB local |
| Buzz generation fails | Missing Gemini API key | Set `GEMINI_API_KEY` in skill .env |

#### Run DynamoDB Local (for checkpoints)

```bash
# Option 1: Docker
docker run -p 8001:8000 amazon/dynamodb-local

# Option 2: Use the backend's mock (if available)
# Set ENVIRONMENT=testing in .env — uses in-memory store

# Create tables locally:
aws dynamodb create-table \
  --endpoint-url http://localhost:8001 \
  --table-name session-history \
  --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

---

### Environment Variables Quick Reference

#### Backend (.env)

```env
ENVIRONMENT=local
OPENAI_API_KEY=sk-...
AWS_REGION=eu-west-1
AWS_ACCESS_KEY_ID=local
AWS_SECRET_ACCESS_KEY=local
DYNAMODB_ENDPOINT=http://localhost:8001    # for local DynamoDB
ORCHESTRATOR_TYPE=langgraph_mcp           # or create_agent
LOG_LEVEL=DEBUG
```

#### Skill Server (.env)

```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
SPHINX_AUTH_URL=https://...
SPHINX_CLIENT_ID=...
SPHINX_CLIENT_SECRET=...
RMA_API_KEY=...
RMA_API_URL=https://...
ENVIRONMENT=local
LOG_LEVEL=DEBUG
```

#### Frontend

```
No .env needed — config is in src/config/environment.ts
The 'local' environment maps to:
  Backend: http://localhost:8000
  CopilotKit: http://localhost:8000/copilotkit
```

---

### Port Map

| Service | Port | URL |
|---------|------|-----|
| LEON Frontend | 3000 | http://localhost:3000 |
| Backend (FastAPI) | 8000 | http://localhost:8000 |
| DynamoDB Local | 8001 | http://localhost:8001 |
| Urgent Drafting Skill | 8003 | http://localhost:8003 |
| Story Drafting Skill | 8004 | http://localhost:8004 |
| Text Archive Skill | 8000 | http://localhost:8000 (conflicts — change if running locally) |

> **Note:** The text-archive skill defaults to port 8000 which conflicts with the backend. When running locally alongside the backend, start it on a different port:
> ```bash
> PORT=8005 uv run python run.py
> ```
