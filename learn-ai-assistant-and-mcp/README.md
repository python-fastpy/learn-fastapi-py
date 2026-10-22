# Add an AI Assistant to Your App, Then Add MCP

A simple reading-list app, grown in three steps, each one run for real
(not described) before being written up here:

```
  STEP 1                STEP 2                       STEP 3
  Plain app     ──▶      + an AI assistant    ──▶      + MCP
  (no AI)                (hardcoded tools)             (tools discovered at
                                                         runtime from a
                                                         separate server --
                                                         this is what makes
                                                         it work like
                                                         Claude Code)
```

**The point of this project:** `reading_list.py` is written **once** and
never changes across all three steps. Only how something *else* reaches
it changes. That's the same lesson `project-book-store` teaches for
swapping a database — here it's swapping how an AI reaches your app.

## The three steps

| Step | File | What it adds |
|---|---|---|
| 1 | [01_plain_app.py](01_plain_app.py) | Nothing AI-related. Four plain functions (`add_book`, `list_books`, `mark_status`, `remove_book`) and a scripted demo. This is "the app." |
| 2 | [02_add_ai_assistant.py](02_add_ai_assistant.py) | A real model, given hand-written tool schemas, decides which function to call from a plain-English request. The assistant's code **imports `reading_list.py` directly** — it has to know the app exists. |
| 3 | [03_add_mcp.py](03_add_mcp.py) + [reading_list_mcp_server.py](reading_list_mcp_server.py) | The same four functions, now wrapped as an MCP server running in its **own process**. The assistant connects over MCP, calls `list_tools()` to discover what's available **at runtime**, and never imports `reading_list.py` at all. |

## Why step 3 is "just like Claude Code"

This is the one-sentence version of the whole project: **Claude Code
doesn't hardcode what tools exist — it launches whatever MCP server your
`.mcp.json` names, asks it what it can do, and uses that.** Step 3's
assistant does the exact same thing, just with one server instead of
several:

```
  step 2                                    step 3 (this project's punchline)
  TOOL_SCHEMAS = [...]   <- hand-written     tools = await client.list_tools()
  TOOLS["add_book"](**args)                  await client.call_tool(name, args)
  (imports reading_list.py directly)         (imports NOTHING app-specific)
```

Point `03_add_mcp.py` at a *different* MCP server — a weather server, a
database server, `learn-fastmcp-server`'s own example server — and the
assistant file does not change. Only which server you launch does. That
swap is precisely what adding a new entry to `.mcp.json` does for Claude
Code itself.

## Setup

```bash
cd learn-ai-assistant-and-mcp
uv sync
```

Steps 2 and 3 need a real model. Same credentials as `learn-agents` and
`learn-mcp` (TR Orchestrator) — copy `.env.example` to `.env` and fill
them in, or run the `fetch-secrets` skill. Step 1 needs nothing.

```bash
uv run python 01_plain_app.py          # no .env needed
uv run python 02_add_ai_assistant.py   # needs .env
uv run python 03_add_mcp.py            # needs .env
```

## How to test it

- **Step 1**: read the printed sequence — add two books, list them, start
  reading one, remove the other, list again. No AI involved; if this
  doesn't work, nothing downstream will either.
- **Step 2**: re-run it a couple of times — the model's phrasing will
  differ, but you should always see `add_book` called before `list_books`
  for the first request, and `add_book` then `mark_status` for the second.
- **Step 3**: the first printed line must say `discovered 4 tools from the
  server` — that's proof the schemas came from `list_tools()`, not from a
  hardcoded list. Everything after should look like step 2's output, just
  with `[mcp call]` instead of `[called]`.
- **Click through the server by hand, with no LLM involved** — the most
  reliable way to isolate "is it the server or the model?" if step 3 ever
  does something unexpected:
  ```bash
  uv run fastmcp dev inspector reading_list_mcp_server.py
  ```
  1. Open the URL it prints (auto-opens in your browser too).
  2. Confirm the sidebar lists all 4 tools — if it's empty, the stdio
     connection failed.
  3. Call `add_book` with `title="Dune"`, `author="Frank Herbert"` →
     expect `{"id": 1, "title": "Dune", ..., "status": "to_read"}`.
  4. Call `list_books` with nothing → expect a list containing that book.
  5. Call `mark_status` with `book_id=1`, `status="reading"` → expect the
     same book back with `"status": "reading"`.
  6. Call `remove_book` with `book_id=1`, then `list_books` again →
     expect an empty list.

  If all five match, the server is proven correct independently of any
  AI. (Same steps are also in `reading_list_mcp_server.py`'s own
  docstring.) **Gotcha:** the Inspector launches its own copy of the
  server with its own empty `BOOKS` list — books added here won't appear
  when you separately run `03_add_mcp.py`, and vice versa.

## Going deeper

This project is deliberately the *minimum* version of "app + AI +
MCP" — three files, one server, no config file, no permission gate, no
CLI loop. Once this makes sense, these are the next steps, which already
exist in this workspace and build on exactly these ideas:

| Want to see... | Go to |
|---|---|
| A real `.mcp.json` config, multiple servers attached at once, a permission gate, a CLI *and* a web UI, hooks, parallel tool calls | [`learn-mini-claude`](../learn-mini-claude/) — this is the fuller version of step 3 |
| The agent loop itself: ReAct, subagents, delegation vs. handoff, memory, named patterns | [`learn-agents`](../learn-agents/) |
| Every FastMCP server feature in depth (what `reading_list_mcp_server.py` only scratches) | [`learn-fastmcp-server`](../learn-fastmcp-server/) |
| Every FastMCP client feature in depth (what step 3's `Client(...)` only scratches) | [`learn-fastmcp-client`](../learn-fastmcp-client/) |
| Production patterns: workflows, orchestration, LangGraph | [`learn-mcp`](../learn-mcp/) |

## Where this sits

This folder exists to answer one specific question as simply as possible:
*"I have an app — how do I add an AI assistant, and how do I make that
assistant use MCP so it behaves like an agentic tool-using assistant?"*
Everything else in the table above goes deeper on one piece of that
question. See [`../AI_ENGINEER_ROADMAP.md`](../AI_ENGINEER_ROADMAP.md) for
how this and every other folder in the workspace fit together.
