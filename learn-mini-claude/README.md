# Learn Mini-Claude — Build Your Own Claude Code (with MCP attached)

Build a working AI coding agent from scratch: an agent loop, file tools
with a sandbox and permission prompts, **any MCP server attached via
`.mcp.json`** (the same config format Claude Code uses), and both a
terminal CLI and a plain HTML/CSS web UI.

The whole agent is ~250 lines. Lessons 01–03 run with **no credentials**.

---

## Architecture — how it works

### The one idea

An AI agent is a **while-loop around a model that can ask for tools**.
The model never executes anything. It emits a tool *name* and some JSON
*arguments*; your code decides whether to run it and feeds the result
back. Everything else here — the sandbox, permission prompts, MCP
servers, the web UI — hangs off that single gap between **ask** and
**run**.

Two data structures carry the whole design:

```python
Tool     = {name, description, parameters-schema, fn, read_only, source}
registry = dict[str, Tool]      # ONE flat dict: built-ins + every MCP tool
```

Once an MCP tool is wrapped into that same `Tool` shape, the loop cannot
tell it apart from a built-in. That's the trick that makes capability a
*config* change instead of a *code* change.

### The parts

```
        ┌──────────────────┐        ┌──────────────────┐
        │  CLI  (04)       │        │  Web UI  (05)    │
        │  terminal REPL   │        │  FastAPI + HTML  │
        │  asks y/n/a      │        │  applies a policy│
        └────────┬─────────┘        └────────┬─────────┘
                 │      both are thin shells │
                 └─────────────┬─────────────┘
                               ▼
        ┌──────────────────────────────────────────────┐
        │              agent_core.py                   │
        │                                              │
        │   agent_loop(model, registry, messages,      │
        │              approve, on_event, usage)       │
        │                                              │
        │   ── the while-loop. Everything below is     │
        │      just what it has access to. ──          │
        └───┬──────────────────┬───────────────────┬───┘
            │                  │                   │
            ▼                  ▼                   ▼
     ┌─────────────┐   ┌───────────────┐   ┌──────────────┐
     │   model     │   │   registry    │   │  approve()   │
     │ llm_helper  │   │ dict[str,Tool]│   │ permission   │
     │ .get_llm()  │   └───────┬───────┘   │ gate         │
     └─────────────┘           │           └──────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
     ┌──────────────────┐            ┌────────────────────────────┐
     │ BUILT-IN tools   │            │  MCP tools (.mcp.json)     │
     │ read_file        │            │                            │
     │ write_file       │            │  notes__*      capability  │
     │ list_files       │            │  workflow__*   procedure   │
     │ run_command      │            │                            │
     │                  │            │  stdio subprocess          │
     │ guarded by       │            │   ── or ── HTTP url        │
     │ safe_path()      │            │                            │
     │ → _sandbox/ only │            │  added by CONFIG, not code │
     └──────────────────┘            └────────────────────────────┘
```

### Startup: building the registry

`build_registry()` runs once, before the first message:

```
1. builtin_tools()          → 4 Tools, hardcoded
2. load_mcp_config()        → read .mcp.json
3. for each server:
     build_transport(cfg)   → StdioTransport (command) or
                              StreamableHttpTransport (url)
     client.list_tools()    → the server tells you what it offers
     make_mcp_tool(...)     → wrap each one in the SAME Tool shape,
                              namespaced  server__toolname
     ↳ on failure: log + skip. One bad server ≠ dead agent.
4. merge everything into one flat dict
```

Discovery happens **at runtime**, which is why you never hand-write tool
specs for an MCP server — it publishes its own JSON Schema.

### What happens when you send a message

Tracing *"Create hello.py that prints hello, then run it."* sent to the
**web UI** — an actual measured run, including the part that gets refused:

```
  you ─────────────────────────────────────────────────────────────┐
                                                                    ▼
  ① messages += HumanMessage(text)
  ② bound = model.bind_tools([t.to_openai_spec() for t in registry])
        └─ all 10 tools described to the model in OpenAI function format

  ── LLM CALL 1 ─────────────────────────────────────────────────────
  ③ reply.tool_calls = [write_file(path='hello.py', content="...")]
  ④ approve(tool, args)?          ← THE GAP. CLI prompts y/n/a.
                                     Web UI applies a policy.
                                     Read-only tools skip this entirely.
  ⑤ safe_path('hello.py')         ← resolve + confirm inside _sandbox/
  ⑥ result = await tool.fn(**args)     → {'written': 'hello.py'}
  ⑦ messages += ToolMessage(result)    ← result re-enters the conversation

  ── LLM CALL 2 ────────────────────────  the WHOLE conversation resent
  ⑧ reply.tool_calls = [run_command(command='python hello.py')]
  ⑨ approve(...) → False          ← web policy blocks run_command
     messages += ToolMessage({'error': 'permission denied by user'})
        └─ a REFUSAL, not a crash. The model reads it and adapts.

  ── LLM CALL 3 ─────────────────────────────────────────────────────
  ⑩ reply.tool_calls is empty  →  plain text  →  LOOP ENDS

  measured: 3 LLM calls · 1,479 tokens in · 83 out
  reply:    "The file hello.py was created… However, I was not able to
             run it due to a permission restriction."
```

Four things worth internalizing from that trace:

1. **One message ≠ one LLM call.** Three calls for one request here.
2. **Every call resends the entire conversation** — that's why input
   (1,479) dwarfs output (83), and why input grows every turn.
3. **A denied tool is a normal result, not an error.** The refusal goes
   back as a `ToolMessage`; the model notices and explains itself instead
   of crashing. Same for a missing file or a failed command.
4. **The loop is capped** (`max_turns=12`). A confused model can otherwise
   call tools forever, and every turn costs money.

> Run the same thing in the **CLI** and step ⑨ becomes a `y/n/a` prompt
> instead — identical loop, different `approve`. That one swapped
> function is the entire difference between the two front ends.

### Where each file fits

| Layer | File | Responsibility |
|-------|------|----------------|
| Front end | `04_mini_claude_cli.py` | Print nicely, prompt `y/n/a`, slash commands |
| Front end | `05_mini_claude_web.py` + `web/` | HTTP endpoints, session state, permission *policy* |
| **Engine** | **`agent_core.py`** | **The loop, the tools, the sandbox, MCP attachment, token accounting** |
| Model | `llm_helper.py` | Auth + endpoint config; returns a LangChain model |
| Capability | `.mcp.json` | Which MCP servers to attach |
| Capability | `demo_mcp_server.py` / `demo_mcp_http.py` | Sample servers to attach |
| Diagnostics | `check_mcp.py` | Did each server actually connect? |

The CLI and the web UI are **not** two agents. They import the same
`agent_loop()` and differ in exactly two functions: how they display
things (`on_event`) and how they answer the permission question
(`approve`). That's the clearest evidence that a UI is a presentation
layer, not the agent.

### The two extension points

Almost anything you'd want to add is one of these:

- **A new capability** → add a `Tool` to the registry. Either write a
  Python function (built-in) or point `.mcp.json` at a server. The loop
  never changes.
- **A new interface** → write something that calls `agent_loop()` with
  its own `approve` and `on_event`. Slack bot, IDE plugin, cron job —
  the agent is already done.

### Reading order

```
01 → the loop alone, mock model, one tool       (no credentials)
02 → real tools, sandbox, permission gate       (no credentials)
03 → MCP attachment, .mcp.json                  (no credentials)
     ── you now understand everything in agent_core.py ──
04 → CLI: the pieces + a real model
05 → Web UI: the same agent, different shell
```

---

## Setup

```bash
cd learn-mini-claude

# 1. Install dependencies (creates .venv automatically)
uv sync

# 2. (Only needed for lessons 04 and 05 — the ones that call a real model)
#    Copy the template and fill in the orchestrator credentials,
#    or run the fetch-secrets skill to populate it.
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
```

That's it. You never start the MCP server yourself — the agent launches
it for you as a subprocess.

---

## Run each lesson

### Lessons 01–03 — no credentials needed

```bash
uv run python 01_agent_loop.py       # the loop, with a mock model
uv run python 02_builtin_tools.py    # file tools + sandbox + permission gate
uv run python 03_attach_mcp.py       # read .mcp.json, attach an MCP server
```

Each prints its output and exits. Read the docstring at the top of the
file first — it explains what you're about to see.

### Lesson 04 — the CLI (needs `.env`)

```bash
uv run python 04_mini_claude_cli.py
```

You get a prompt. Try, in order:

```
> list the files you can see
> create hello.py that prints the first 10 fibonacci numbers
> run it
> save a note saying the demo works        <- this one goes to the MCP server
> /tools                                    <- shows builtin vs MCP tools
> /exit
```

Write and shell commands ask permission: `y` (once), `n` (refuse),
`a` (allow that tool for the rest of the session).

### Lesson 05 — the web UI (needs `.env`)

```bash
uv run python 05_mini_claude_web.py
```

Then open **http://127.0.0.1:8100** in your browser. Same agent, same
tools, in a chat window. Tool calls appear as chips under each reply —
hover a chip to see the arguments. `Ctrl+C` in the terminal to stop.

> The web UI refuses `run_command` by design — an HTTP handler can't stop
> and ask you mid-request. See the permission-policy note in lesson 05.

### What to type

Paste these into the web UI input box (or the CLI prompt) in order — each
one exercises a different part of the system.

**Built-in tools**

```
list the files you can see
create hello.py that prints the first 10 fibonacci numbers
read hello.py back to me
run it                                    ← CLI only; the web UI blocks shell
```

**MCP tools** (the notes server)

```
save a note saying the demo works, tagged demo
list my notes
```

**Workflows** (the workflow server drives the agent step by step)

```
what workflows are available?
use the new-script workflow to create primes.py that prints the first 10 primes. follow every step.
use the code-review workflow on hello.py. follow every step.
```

> Name the workflow **and** say *"follow every step."* Without that the
> agent usually ignores the workflow tools and just does the task
> directly — which is faster, but skips the procedure you wanted enforced.

**Seeing the guardrails fire**

```
read ../../.env                           ← blocked by the sandbox
delete everything in the folder           ← needs permission; say no
```

**CLI-only commands**

```
/tools     every tool and where it came from
/usage     tokens and cost so far
/clear     forget the conversation
/exit
```

---

## Custom prompts — telling the agent how to behave

The system prompt is built from three layers, assembled by
`build_system_prompt()` in `agent_core.py`:

| Layer | Where | Scope | Survives restart? |
|-------|-------|-------|-------------------|
| 1. Base rules | `BASE_SYSTEM_PROMPT` in `agent_core.py` | Always | yes (it's code) |
| 2. Project instructions | **`AGENT.md`** | Every session | **yes** |
| 3. Session instructions | UI panel / CLI `/system` | One conversation | no |

Later layers are appended last, which is also where a model weights them
most heavily — so the more specific instruction wins when two disagree.

### AGENT.md — persistent instructions

[`AGENT.md`](AGENT.md) is this project's `CLAUDE.md`. Its whole contents
are appended to the system prompt on every run. Edit it, restart (or
`/clear` in the CLI, which re-reads it), done.

The shipped file has deliberately checkable rules, so you can prove it's
being read. Ask for a script and watch:

```
> create greet.py that prints hello world
```
```python
# Prints 'hello world' to the console      ← AGENT.md: scripts start with a # comment
print('hello world')
```
> *"Created greet.py… Run it with: python greet.py"* ← AGENT.md: say how to run it

Delete those rules and write your own. Real uses: coding standards,
"always run the tests after editing", domain vocabulary, which libraries
to prefer.

### Per-session instructions

**Web UI** — click **custom prompt** in the tool bar, type into the panel,
hit **Apply & restart chat**. It's saved in `localStorage`, so it
survives a page reload. **View full prompt** shows exactly what the model
is being told — the fastest way to confirm your text landed.

**CLI:**

```
/system Reply only in bullet points.   set instructions for this session
/system                                clear them
/prompt                                print the full system prompt in effect
/clear                                 restart the chat, re-reading AGENT.md
```

A real run with `system_extra` set to *"Reply ONLY as a numbered list.
Never write prose sentences."*:

```
> list the files you can see
1. buggy.py
2. fib.py
3. greet.py
...
```

> **Changing the prompt restarts the conversation.** The system prompt is
> `messages[0]`, and you can't retroactively change instructions the model
> has already been answering under. Both UIs make this explicit rather
> than silently applying a new prompt to an old conversation.

> **The prompt is not a security boundary.** "Never touch files outside
> the project" in `AGENT.md` is a *request*; `safe_path()` is the
> *enforcement*. See [Safety](#safety) — prompts shape behaviour, code
> constrains it.

## Attaching your own MCP server

Edit [`.mcp.json`](.mcp.json). Two kinds of server are supported:

```jsonc
{
  "mcpServers": {
    // A) local script — the agent launches it as a subprocess (stdio)
    "notes": {
      "command": "python",
      "args": ["demo_mcp_server.py"]
    },

    // B) a server already running somewhere (HTTP)
    "remote": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Restart the CLI or web server and the new tools appear automatically —
namespaced as `servername__toolname`. **No agent code changes.**

This is the same format Claude Code reads, so any MCP server you already
use with Claude Code works here unchanged, and vice versa.

### The workflow server — making the agent follow a procedure

Two MCP servers ship here, and they do different jobs:

| Server | Adds | Example |
|---|---|---|
| `demo_mcp_server.py` (notes) | **Capability** — new things the agent *can* do | `save_note`, `list_notes` |
| `workflow_mcp_server.py` | **Procedure** — an order it *must* work through | `start_workflow`, `complete_step` |

Left alone, an agent improvises. Ask it to "write a script" and it will
happily write one and declare success **without ever running it**. A
workflow turns "run it" into a step the server hands out and tracks — the
agent can't reach the end without passing through it.

Workflows are markdown files with YAML frontmatter, in
**[`workflows/`](workflows/)**:

- [`workflows/new-script.md`](workflows/new-script.md) — write a script → run it → record it
- [`workflows/code-review.md`](workflows/code-review.md) — read a file → find bugs → write a report

```markdown
---
name: new-script
description: Create a Python script, verify it runs, and record it in notes
steps:
  - Write the script to <target> using write_file.
  - Run it with run_command and check the exit code is 0.
  - If it failed, fix the script and run it again before continuing.
  - Save a note via notes__save_note summarising it, tagged "script".
---

Free-text guidance goes here. It's handed to the agent with step 1.
```

`<target>` is substituted with whatever file the workflow is started on.
Drop in a new `.md`, restart, and it's available — **no code change**. A
single `workflow.md` next to the script also works if you prefer one file.

Check they parse without starting anything:

```bash
uv run python workflow_mcp_server.py --list
```

**How it drives the agent** — the server holds the run state, so it only
ever hands out the *current* step:

```
agent : start_workflow("new-script", target="fib.py")
server: → run_id=wf-1 · step 1/4 "Write the script to fib.py…"
agent : (write_file)  → complete_step(wf-1, "wrote fib.py")
server: → step 2/4 "Run it with run_command…"
agent : (run_command) → complete_step(wf-1, "exit code 0")
                      … → "Workflow complete (4/4 steps)."
```

Try it — type one of these into the web UI or CLI:

```
what workflows are available?
use the new-script workflow to create fib.py that prints the first 8 fibonacci numbers. follow every step.
use the code-review workflow on fib.py. follow every step.
```

A real run of the second one, in the web UI:

```
[call]   workflow__list_workflows
[call]   workflow__start_workflow
[call]   write_file                  ← step 1
[call]   workflow__complete_step
[denied] run_command                 ← step 2, blocked by the web policy
[call]   workflow__complete_step        …recorded WITH the caveat
[call]   workflow__complete_step      ← step 3, no fix needed
[call]   notes__save_note             ← step 4, a different MCP server
[call]   workflow__complete_step      → complete

10 LLM calls · 11,536 tokens in · 345 out · ~$0.018
```

Two things that run shows:

- **The markdown steers behaviour.** `new-script.md` says that if
  `run_command` is unavailable, say so explicitly rather than skipping
  silently — and that's exactly what happened when the web policy blocked
  it. Guidance in the file, not in the agent's code.
- **Workflows are expensive.** 10 LLM calls versus 2–3 for the same task
  asked directly, because every `complete_step` is another round-trip
  resending the conversation. You're buying reliability with tokens.
  Worth it for procedures that must not be skipped; wasteful for
  one-liners.

> Compare with `learn-mcp` lesson 09, which uses workflows to **gate**
> tools (hide what's irrelevant). This one **sequences** work and keeps
> state. Both are real patterns and they compose.

### Testing a workflow

Three levels, cheapest first. Use the first two while you're writing the
`.md`; save the third for when you think it's right.

**1. Does it parse?** (instant, no server)

```bash
uv run python workflow_mcp_server.py --list
```

**2. Does the state machine work?** (seconds, **zero tokens**)

```bash
uv run python test_workflow.py                # every workflow
uv run python test_workflow.py code-review    # just one
```

`test_workflow.py` plays the agent's part mechanically — start, then
`complete_step` until done — so it tests *your `.md` and the server*,
not the model's mood. 15 checks per workflow: every step handed out in
order exactly once, `<target>` substituted, run reaches `complete` with
a full log, `workflow_status` doesn't advance the run, bad input
rejected, and **every tool name in a step actually exists**.

That last one earns its keep. MCP tools are namespaced with a *double*
underscore, and writing one is invisible by eye:

```
[FAIL] step tool names all exist -- notes_save_note -> notes__save_note
```

Exit code is 0/1, so it drops into CI.

**Check the harness can actually fail.** A test suite you've never seen
go red isn't yet a test suite — this check was initially broken and
silently passed the very typo it exists to catch. Prove it works:

```bash
# 1. Write a deliberately broken workflow
#    workflows/_broken.md
#      ---
#      name: broken-demo
#      description: Deliberately broken
#      steps:
#        - Save it with notes_save_note   <- ONE underscore, should be two
#      ---

uv run python test_workflow.py broken-demo   # expect FAIL + exit 1
rm workflows/_broken.md                      # PowerShell: Remove-Item
```

**3. Does the agent actually follow it?** (~30s, ~$0.02, needs `.env`)

Only this level tests the wording — whether the model reads your step and
does the right thing. Type into the web UI or CLI:

```
Use the code-review workflow on buggy.py. Follow every step.
```

Watch the tool chips appear in order. A real run:

```
workflow__start_workflow → read_file → complete_step → complete_step
  → write_file → complete_step → notes__save_note → complete_step
9 LLM calls · 11,423 tokens · ~$0.018
```

> **What level 3 can and can't tell you.** It proves the *procedure* ran.
> It does not prove the *judgment* was sound. In the run above the agent
> correctly found both real bugs — then invented a third ("SyntaxError,
> extra closing parenthesis") that wasn't in the file, despite
> `code-review.md` explicitly saying not to. A workflow enforces which
> steps happen, not the quality of the thinking inside them. For that you
> need output evals — see `learn-ai-advanced` lesson 02.

### Checking a server is actually connected

```bash
uv run python check_mcp.py
```

It tests every server in `.mcp.json` and, for URL servers, separates the
two things that fail independently:

```
[notes]  stdio  ->  python demo_mcp_server.py
  mcp       : OK  (3 tools, 1598ms)
     - notes__save_note   Save a note to the persistent notes store.

[notes_http]  http  ->  http://127.0.0.1:8200/mcp
  reachable : YES  (HTTP 405)
  mcp       : OK  (3 tools, 367ms)

[broken_demo]  http  ->  http://127.0.0.1:9999/mcp
  reachable : NO  (connection refused / host not found)
  mcp       : SKIPPED -- nothing listening at that URL
```

Reading the result:

| What you see | What it means | Fix |
|---|---|---|
| `reachable: NO` | Nothing is listening there | Start the server; check host/port |
| `reachable: YES` + `mcp: FAILED` | Something answered, but it isn't MCP at that path | Usually a missing `/mcp` on the end of the URL |
| `mcp: OK` | Connected; those tools are live | — |

`reachable: YES (HTTP 405/404)` is normal — MCP endpoints reject a plain
`GET`. Reachability only asks "did anything answer", not "is it happy".

Exit code is `0` only if every server connected, so it works in CI.

Other quick checks:
- `uv run python 03_attach_mcp.py` — lists what got attached
- `/tools` in the CLI, or the pill in the web UI header
- `curl http://127.0.0.1:8100/tools` while the web UI is running — look
  for `"source": "mcp:<name>"`

**The registry is built once at startup.** After editing `.mcp.json`,
restart the CLI or web server — it won't hot-reload.

If a server fails, the agent still starts and just skips it, so a broken
entry costs you that server's tools rather than the whole session.

### Trying a URL server locally

`demo_mcp_http.py` serves the same notes tools over HTTP so you can test
the `url` style without writing a second server:

```bash
# terminal 1
uv run python demo_mcp_http.py          # serves on http://127.0.0.1:8200/mcp

# terminal 2 — add to .mcp.json, then:
uv run python check_mcp.py
```

```jsonc
"notes_http": { "url": "http://127.0.0.1:8200/mcp" }   // note the /mcp
```

> **Windows note:** save `.mcp.json` as UTF-8 **without BOM**. PowerShell's
> `Out-File -Encoding utf8` adds a BOM that breaks JSON parsers. The
> loader here uses `utf-8-sig` so it tolerates one, but other tools won't.

---

## Lesson Index

| # | File | What You Learn | Needs `.env`? |
|---|------|----------------|---------------|
| 01 | `01_agent_loop.py` | The 4-step agent loop; what a "tool" is to a model; turn limits | No |
| 02 | `02_builtin_tools.py` | read/write/list/run tools, path sandboxing, the permission gate | No |
| 03 | `03_attach_mcp.py` | `.mcp.json`, runtime tool discovery, adapting MCP tools, namespacing, failure isolation | No |
| 04 | `04_mini_claude_cli.py` | The full terminal REPL: real LLM, conversation state, y/n/a prompts, slash commands | **Yes** |
| 05 | `05_mini_claude_web.py` | FastAPI + HTML/CSS chat UI, session state, permission *policy* vs. prompt | **Yes** |

### Supporting files

| File | Purpose |
|------|---------|
| `agent_core.py` | Lessons 01–03 assembled into one module. Both 04 and 05 import it — the agent itself is written once. |
| `demo_mcp_server.py` | A tiny MCP server (a notes store) so `.mcp.json` points at something real out of the box. Built with FastMCP — see `learn-mcp`. |
| `demo_mcp_http.py` | The same notes server over HTTP, for testing `url`-style entries. |
| `workflow_mcp_server.py` | A stateful MCP server that walks the agent through a procedure, one step at a time. |
| `workflows/*.md` | The workflow definitions — markdown + YAML frontmatter. Add a file, restart, done. |
| `test_workflow.py` | Tests a workflow end to end with **no LLM and no tokens**. |
| `check_mcp.py` | Diagnostic — is each server in `.mcp.json` actually connected? |
| `.mcp.json` | The server config. Edit this to attach your own. |
| `AGENT.md` | Persistent instructions appended to the system prompt — this project's `CLAUDE.md`. |
| `web/index.html`, `web/style.css` | The whole front end. No React, no npm, no build step. |
| `llm_helper.py` | TR Orchestrator auth — same helper as `learn-mcp`/`learn-langgraph`. |

---

## Token usage and cost

Both UIs report tokens. In the CLI, every turn prints a line and `/usage`
shows the session total:

```
  [1076 tokens (1001 in, 75 out) in 2 calls  ~$0.0026  |  session 1447 tok ~$0.0031]
```

In the web UI: a line under each reply, and a running total in the header.

**The number that surprises people is `calls`.** One user message is not
one LLM call — each tool round-trip is another call, and *each one resends
the whole conversation so far*. A two-tool request costs three calls, and
by turn 10 you're re-sending turns 1–9 every time. That's why input tokens
dwarf output tokens (1001 in vs 75 out above) and why long sessions get
expensive faster than you'd expect.

Two things that fight it, both real features of Claude Code:
- **Prompt caching** — repeated prefixes are billed at a discount. Tracked
  separately as `cached`; `agent_core.PRICING` prices it at 1/4 of input.
- **Compaction** — summarize old turns and drop them, so the resent prefix
  stops growing. That's exercise 3 in lesson 04.

> Costs are **estimates** from public list prices in `agent_core.PRICING`,
> not a billing source. Update those rates for your actual model.

## Safety

Everything the agent touches is confined to `_sandbox/` (created on first
run). `safe_path()` resolves each path and rejects anything that escapes,
**before** the tool runs — so approving a prompt still can't reach outside
the sandbox. Delete `_sandbox/` any time to reset.

Two controls, in this order:

1. **Sandbox** — structural, not negotiable. Path resolved and checked.
2. **Permission gate** — your judgment call. Reads auto-approve; writes
   and shell commands ask (CLI) or follow a policy (web).

---

## How this maps to real Claude Code

| This folder | Real Claude Code |
|-------------|------------------|
| `agent_loop()` | The same loop — model asks for tools, harness runs them, results go back |
| `read_file` / `write_file` / `run_command` | Read / Write / Edit / Bash tools |
| `safe_path()` + `permission_gate()` | Permission modes and allow/deny rules in `settings.json` |
| `.mcp.json` | Identical format — servers are portable between the two |
| `AGENT.md` | `CLAUDE.md` — project instructions appended to the system prompt |
| `SESSION_ALLOW` (`a` option) | "Always allow" in the permission prompt |
| `max_turns` | Turn/budget limits on an agentic run |

What real Claude Code adds isn't a different architecture — it's depth:
smarter tools (Edit with ambiguity checks, Grep/Glob), context compaction,
subagents, hooks, streaming, and a great deal of prompt engineering.

## Related lessons in this repo

| Topic | Where |
|-------|-------|
| Building MCP servers properly | `learn-mcp` lessons 01–09 |
| Multi-server routing, MCP-to-MCP | `learn-mcp` lessons 11, 15 |
| Agent vs. MCP, handoffs, supervisors | `learn-mcp` lesson 16 |
| The same loop as a state machine | `learn-langgraph` lesson 07 |
| Pausing to ask the user (interrupt/resume) | `learn-mcp` lesson 10, `learn-langgraph` lesson 09 |
| Prompt injection via poisoned tool output | `learn-ai-advanced` lesson 04 |
| Tracing tool calls, token cost | `learn-ai-advanced` lesson 03 |
| Session storage beyond in-memory | `fastapi/08-session.py` |
