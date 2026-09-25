# Learn LLM Fundamentals: How LLMs Work, Context Engineering, and the Path to AI Engineer

What an LLM really is, how every setting (temperature, top_p, top_k,
penalties, max_tokens, stop) changes its output, what an API call
actually sends, how **tools** work and how to build the six common
kinds safely, and the discipline that matters most in real AI apps:
**context engineering**. It ends with a roadmap that maps every
AI-engineer skill to the folder in this repo that teaches it.

All 8 lessons are **pure Python: no packages, no API keys**. Every
number in this README comes from running them.

```bash
cd learn-llm-fundamentals
uv run python 01_what_is_an_llm.py      # or plain: python 01_what_is_an_llm.py
uv run python 02_sampling_temperature_top_p.py
uv run python 03_chat_api_anatomy.py
uv run python 07_tool_calling.py         # tools: read these two right after 03
uv run python 08_tool_types_catalogue.py
uv run python 04_context_engineering.py
uv run python 05_prompt_engineering.py
uv run python 06_production_llm_engineering.py
```

**How to use this:** read a section below, run the matching lesson,
then do the exercises at the bottom of the file. Each file's docstring
has the diagram and the list of concepts.

---

## Contents

1. [What an LLM is](#1-what-an-llm-is) (lesson 01)
2. [Sampling: temperature, top_p, top_k and every other knob](#2-sampling-temperature-top_p-top_k-and-every-other-knob) (lesson 02)
3. [What an API call really is](#3-what-an-api-call-really-is) (lesson 03)
   - [3b. Tools: function calling and the tool catalogue](#3b-tools-function-calling-and-the-tool-catalogue) (lessons 07, 08)
4. [No-confusion FAQ](#4-no-confusion-faq)
5. [Context engineering](#5-context-engineering) (lesson 04)
6. [Prompt engineering](#6-prompt-engineering) (lesson 05)
7. [Production engineering](#7-production-engineering) (lesson 06)
8. [The AI engineer roadmap](#8-the-ai-engineer-roadmap)
9. [Glossary](#9-glossary)

---

## 1. What an LLM is

### The one sentence

> An LLM is a function that takes a sequence of **tokens** and returns a
> **probability for every possible next token**. Nothing more.

Chat, code, tool calls, "reasoning" and agents are all that function
called in a loop, with engineering around it.

### Two phases: training (once, by the provider) vs inference (every call, by you)

```
 TRAINING -- done by OpenAI / Anthropic / Meta ... months, $$$$$$
 ─────────────────────────────────────────────────────────────────
  1. Pre-training     trillions of tokens of text/code
                      objective: predict the next token
                      result: a "base model" -- autocompletes anything
        │
        ▼
  2. Instruction       curated (prompt, good answer) pairs
     tuning (SFT)      result: follows instructions, chats
        │
        ▼
  3. Preference        humans / AI rate answers; model is nudged toward
     tuning (RLHF,     the preferred ones. Also: reasoning training,
     RLAIF, ...)       safety training, tool-use training
        │
        ▼
     FROZEN WEIGHTS  ── ship ──►  the model you call via the API

 INFERENCE -- what happens on EVERY API call you make. Weights never change.
 ─────────────────────────────────────────────────────────────────
  your text ─► tokenizer ─► [ids] ─► model ─► P(next token) ─► sampling ─► 1 token
                               ▲                                            │
                               └──────────── append it, run again ──────────┘
                                   (until end-of-turn, stop sequence, or max_tokens)
```

**Nothing you send ever changes the model.** Your prompt, your
feedback, your conversation: none of it trains the model you're
talking to. "Memory" is always your code resending text.

### Tokens

```
 "The cat sat on the mat."  ──►  ['The', ' cat', ' sat', ' on', ' the', ' mat', '.']   7 tokens
 " unbelievable"            ──►  [' un', 'believ', 'able']                             3 tokens
```

| Rule of thumb (English) | |
|---|---|
| 1 token | ≈ 4 characters ≈ ¾ of a word |
| 1,000 tokens | ≈ 750 words ≈ 1.5 pages |
| Code, JSON, numbers, non-English | noticeably **more** tokens per character |

Tokens are the unit of **everything**: price, speed, context-window
size, `max_tokens`. Models see tokens, not letters, which is why
"count the r's in strawberry" is hard for them.

### The context window

```
 ┌─────────────────────── context window (e.g. 128k, 200k, 1M tokens) ───────────────────────┐
 │  system prompt │ tools │ docs │ conversation history │ tool results │ question ║  OUTPUT   │
 │◄──────────────────────────────── input tokens ─────────────────────────────────►║◄max_tok─►│
 └────────────────────────────────────────────────────────────────────────────────────────────┘
   everything the model can "see" on this call          reserve room for the answer
```

- It's **per call**. Nothing outside it exists for the model.
- **Input + output share it.** A 128k window full of input leaves no room to answer.
- Bigger isn't free: more input means more cost, a slower first token,
  and more for the model to get distracted by (see section 5).

### Why it hallucinates, and why context fixes it

Lesson 01 trains a tiny model on only **true** sentences, like "paris
is the capital of france". It then generates **false** ones:

```
 200 generations from 'paris is the capital'  (model sees 1 word back)
    57x  'paris is the capital of italy .'      FALSE
    47x  'paris is the capital of germany .'    FALSE
    40x  'paris is the capital of france .'     TRUE

 wrong answers vs how far back the model can see:
    sees 1 word : 111/200 wrong
    sees 3 words: 104/200 wrong
    sees 5 words:   0/200 wrong      <- can finally see 'paris' when choosing the country
```

Each step is locally plausible ("of" → a country); nothing checks the
whole claim. **Fluent-but-wrong is the default failure mode.** The fix
is getting the right information into what the model can see. Real
models see their whole context window, so *what you put in it* is the
biggest lever you control.

### What an LLM is and isn't

| Myth | Reality |
|---|---|
| It looks things up in a database | It predicts tokens from patterns in its weights. No lookup unless **you** give it tools or retrieval |
| It remembers our previous chats | The API is stateless. Your app resends history, or saves "memories" and re-injects them |
| It learns from my corrections | Not during your session. Weights are frozen; only the context changes |
| It knows today's news | It knows its training data up to a **knowledge cutoff**, plus whatever is in the context |
| Temperature 0 means correct | Temperature 0 means *most likely*. A confident wrong answer is still wrong |
| It runs my code / calls my API | It **writes a request** for a tool; your code runs it (see `learn-mini-claude`) |
| A bigger context window fixes everything | More tokens = more cost, latency and distraction. Select, don't stuff |

### LLM vs agent vs subagent

| Layer | What it is | Memory |
|---|---|---|
| **LLM** | `messages → text`. Can't act | None. You resend history |
| **Agent** | LLM + tools + a loop | Its `messages` list |
| **Subagent** | An agent another agent calls as a tool | Its own fresh list; parent gets only the summary |

Runnable side by side in [`learn-mini-claude/06_llm_vs_agent_vs_subagent.py`](../learn-mini-claude/06_llm_vs_agent_vs_subagent.py).

---

## 2. Sampling: temperature, top_p, top_k and every other knob

### The pipeline: where every knob acts

```
 model output: one LOGIT (raw score) per vocabulary token
      │
      │  ① frequency / presence penalty ── lower logits of tokens already used
      ▼
      │  ② ÷ temperature                ── T<1 sharpen · T=1 unchanged · T>1 flatten · T=0 greedy
      ▼
   softmax  ──► probabilities (sum to 1)
      │
      │  ③ top_k   ── keep only the k most likely tokens
      │  ④ top_p   ── keep the smallest set whose probability adds up to p
      │  (renormalize so the survivors sum to 1)
      ▼
   random pick (seeded) ──► ONE token
      │
      │  ⑤ stop sequence matched?  ⑥ max_tokens reached?  ⑦ model emitted end-of-turn?
      ▼
   yes → stop (stop_reason tells you which)      no → append token, run the model again
```

**None of these make the model smarter or add knowledge.** They only
decide how one token is chosen from what the model already predicted.
If answers are *wrong*, fix the context. If they're *too random* or
*too repetitive*, fix the sampling.

### Temperature: every case, measured

Next token after *"The weather today is"* (lesson 02, 1000 samples per row):

| T | sunny | cloudy | rainy | cold | perfect | purple | banana | nonsense picks / 1000 |
|---|---|---|---|---|---|---|---|---|
| **0** | 100% | 0 | 0 | 0 | 0 | 0 | 0 | 0 (greedy: always the top token) |
| 0.2 | 94.9% | 4.7% | 0.4% | 0 | 0 | 0 | 0 | 0 |
| 0.5 | 68.7% | 20.7% | 7.6% | 2.3% | 0.7% | 0.0% | 0.0% | 1 |
| 0.7 | 56.8% | 24.1% | 11.8% | 5.0% | 2.1% | 0.1% | 0.0% | 5 |
| **1.0** | 45.8% | 25.1% | 15.2% | 8.4% | 4.6% | 0.7% | 0.2% | 14 (the model's own distribution) |
| 1.5 | 36.1% | 24.2% | 17.3% | 11.6% | 7.8% | 2.2% | 0.8% | 36 |
| 2.0 | 30.8% | 22.8% | 17.8% | 13.2% | 9.8% | 3.8% | 1.8% | 66 |

```
 T=0    ████████████████████████████████████████ sunny      one answer, every time
 T=1    ██████████████████ sunny ██████████ cloudy ██████ rainy ███ cold ██ perfect ▏purple ▏banana
 T=2    ████████████ sunny █████████ cloudy ███████ rainy █████ cold ████ perfect █▌purple ▌banana
```

Low T concentrates probability on the top token. High T spreads it
into the tail, and over hundreds of tokens small tail picks compound
into incoherent text.

### top_k and top_p: cutting off the tail

| Setting | Keeps (T=1.0) | Behaviour |
|---|---|---|
| `top_k=1` | sunny | Greedy, same as T=0 |
| `top_k=3` | sunny, cloudy, rainy | Always exactly 3, however confident the model is |
| `top_p=0.5` | sunny, cloudy | Smallest set reaching 50% |
| `top_p=0.9` | sunny, cloudy, rainy, cold | Smallest set reaching 90% |
| `top_p=1.0` | all 7 | No filtering |

**top_p adapts, top_k doesn't.** With the same `top_p=0.9`:

```
 "The capital of France is"  (model is sure)    → keeps 1 token : Paris
 "My favourite colour is"    (model is unsure)  → keeps 5 tokens: red, blue, green, black, white
```

### Combinations: every case

Temperature runs **first**, so it changes what top_p sees.

| Setting | Result | Use it? |
|---|---|---|
| `T=0` (+ anything) | Always the top token. top_p/top_k have nothing to cut | ✅ extraction, classification, tests |
| `T=0.2–0.3`, `top_p=1` | Almost always the top token, tiny variation | ✅ code, RAG, agents, JSON |
| `T=0.7`, `top_p=1` | Varied but sensible | ✅ general chat default |
| `T=1`, `top_p=0.9` | Model's own distribution, junk tail removed | ✅ creative writing |
| `T=1.5`, `top_p=0.9` | Flattened, so the **same** 0.9 keeps 5 tokens instead of 4 | ⚠️ brainstorming only |
| `T=0.5`, `top_p=0.9` | Sharpened, so 0.9 keeps just 3 tokens | ✅ fine, but pick one knob |
| `T=1`, `top_k=3`, `top_p=0.9` | top_k cuts to 3, then top_p keeps all 3 | ⚠️ hard to reason about |
| `T=2`, `top_p=1` | Tail fully awake: nonsense within a few sentences | ❌ |
| `T=0`, `top_p=0.1` | Same as T=0 | Redundant |

**Rule:** tune **one** of temperature or top_p and leave the other at
its default. Some APIs enforce this (see the provider table below).

### The other knobs

| Knob | What it does | Demo result (lesson 02) | Gotcha |
|---|---|---|---|
| `max_tokens` | Hard cap on **output** tokens (not input) | Stops at `'Step 1: boil water.\nStep'` | Truncated output; a cut-off JSON won't parse. **Check `stop_reason`** |
| `stop` / `stop_sequences` | End generation when a string appears; the string is removed | Ends before "Step 3" | Choose strings that can't appear in the normal answer |
| `frequency_penalty` | Lowers a token's logit by `penalty × times used` | `very very very…` → `very very good .` | Too high: avoids words it *must* repeat (names, variables) |
| `presence_penalty` | Flat decrease once a token has appeared at all | → `very good .` | Same |
| `seed` | Same seed + same settings → (usually) same picks | Seed 7 twice: identical | **Best-effort only** on real APIs |

**Determinism:** even at `T=0`, real APIs aren't fully deterministic:
GPU floating-point order, batching and model updates can flip near-ties.
Don't write tests that assert exact wording. Assert structure and facts
(evals: `learn-ai-advanced/02`).

### What to set, by task

| Task | temperature | top_p | Why |
|---|---|---|---|
| Extraction, classification, JSON | 0–0.2 | 1.0 | One right answer; variety = bugs |
| Code generation | 0–0.3 | 1.0 | Syntax punishes creative tokens |
| RAG / factual Q&A | 0–0.3 | 1.0 | Stick to the retrieved text |
| Agents / tool calling | 0–0.3 | 1.0 | Reliable tool names and arguments |
| General chat | 0.5–0.8 | 1.0 | Natural, not robotic |
| Creative writing, brainstorming | 0.8–1.2 | 0.9–1.0 | Variety is the goal |
| N diverse candidates → pick best | 0.9–1.2 | 0.95 | Explore, then judge (self-consistency, lesson 05) |

### Provider differences: check your model's docs

| Model family | temperature | top_p / top_k | Other |
|---|---|---|---|
| OpenAI chat models (e.g. GPT-4.1, GPT-4o) | 0–2 | top_p 0–1 | `frequency_penalty`, `presence_penalty`, `seed`, `stop` |
| OpenAI reasoning models (o-series) | not configurable | not configurable | steer with reasoning effort |
| Claude models that accept sampling (e.g. Haiku 4.5, Sonnet/Opus 4.6) | 0–1 | top_p, top_k | `stop_sequences` |
| Newest Claude models (Opus 4.7+, Opus 5.x, Sonnet 5, Fable 5.x) | **rejected** (400 error) | **rejected** | steer with the prompt and `output_config.effort` |

The trend: newer and reasoning models manage sampling themselves, and
the knob you get is **how much to think**, not how random to be. This
changes often, so always check the current docs for your exact model.

### How to set them in code

**This repo's helper** (Azure OpenAI through the TR orchestrator, used by `learn-mini-claude`, `learn-mcp`, etc.):

```python
from llm_helper import get_llm
llm = get_llm(model="gpt-4-1", temperature=0.2)          # temperature is a get_llm() argument
reply = await llm.ainvoke(messages, stop=["\n\n"])        # stop sequences per call (LangChain)
```

**OpenAI SDK:**

```python
from openai import OpenAI
client = OpenAI()
resp = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "system", "content": "You are terse."},
              {"role": "user", "content": "Name 3 rainy-day activities."}],
    temperature=0.7,          # OR top_p -- tune one
    max_tokens=200,
    stop=["\n\n"],
    seed=42,                  # best-effort reproducibility
)
choice = resp.choices[0]
print(choice.message.content, choice.finish_reason, resp.usage)   # ALWAYS check finish_reason
```

**Anthropic SDK:**

```python
import anthropic
client = anthropic.Anthropic()

# A model that accepts sampling params
resp = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=200,
    temperature=0.2,          # 0-1 on Claude
    stop_sequences=["\n\n"],
    system="You are terse.",
    messages=[{"role": "user", "content": "Name 3 rainy-day activities."}],
)

# Newest models: no temperature/top_p/top_k -- control depth/cost with effort instead
resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=16000,
    output_config={"effort": "low"},   # low | medium | high | xhigh | max
    messages=[{"role": "user", "content": "Name 3 rainy-day activities."}],
)
for block in resp.content:
    if block.type == "text":
        print(block.text)
print(resp.stop_reason, resp.usage)   # ALWAYS check stop_reason
```

---

## 3. What an API call really is

### Request → model → response

```
 YOUR REQUEST (JSON)                          WHAT THE MODEL SEES (one token stream)
 ┌───────────────────────────────┐           ┌───────────────────────────────────────┐
 │ model: "..."                  │           │ <|system|>You are terse.              │
 │ system: "You are terse."      │  chat     │ Tools available: [...]<|end|>         │
 │ tools: [get_weather(...)]     │ template  │ <|user|>What is 2+2?<|end|>           │
 │ messages:                     │ ────────► │ <|assistant|>4<|end|>                 │
 │   user: "What is 2+2?"        │           │ <|user|>And times 3?<|end|>           │
 │   assistant: "4"              │           │ <|assistant|>   ◄── continues here    │
 │   user: "And times 3?"        │           └───────────────────────────────────────┘
 │ temperature, max_tokens, stop │                          │  the lesson 01 loop
 └───────────────────────────────┘                          ▼
 YOUR RESPONSE (JSON)
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │ content:     [{type: "text", text: "12"}]   or   tool_calls: [{name, arguments}] │
 │ stop_reason: end_turn | max_tokens | tool_use | stop_sequence | refusal          │
 │ usage:       {input_tokens: 41, output_tokens: 2, cache_read_input_tokens: 0}    │
 └──────────────────────────────────────────────────────────────────────────────────┘
```

Roles are just marker tokens in one stream. That's why text that
*says* "ignore your instructions" inside a document or tool result can
work: prompt injection (`learn-ai-advanced/04`).

### The four roles

| Role | Written by | Used for |
|---|---|---|
| `system` | You (developer) | Persona, rules, format, tool policy. Sent every call |
| `user` | End user / your code | The request; also retrieved docs, files, examples |
| `assistant` | The model | Its earlier replies, which you send back so it knows what it said |
| `tool` | Your code | A tool's result, linked to the model's tool-call id |

### Stateless: every call resends everything

```
 call 1:  [system][u1]                         → a1
 call 2:  [system][u1][a1][u2]                 → a2
 call 3:  [system][u1][a1][u2][a2][u3]         → a3      input grows every turn
 call N:  [system][u1][a1] ... [u_N]           → a_N     → cost, latency, context limit
```

Measured in lesson 03: 5 short turns bill **458 input tokens vs 84
output**. In agents and RAG, input usually dominates the bill:

| Request | In | Out | Cost | Input share |
|---|---|---|---|---|
| Chat reply | 1,500 | 300 | $0.0090 | 50% |
| RAG answer (8 chunks) | 6,000 | 400 | $0.0240 | 75% |
| Agent turn 10 | 40,000 | 200 | $0.1230 | 98% |
| Agent turn 10 **with prompt caching** | 40,000 | 200 | **$0.0258** | 88% |

*(example rates: $3/1M input, $15/1M output, $0.30/1M cached)*

### Tool calls and JSON are text the model writes

```
 you send tool schema ─► model WRITES {"name":"get_weather","arguments":{"city":"Rome"}}
                        ─► API parses it into tool_calls, stop_reason="tool_use"
                        ─► YOUR code runs it ─► you send the result back ─► model continues
```

Structured output has three layers, strongest last:
1. Ask for JSON in the prompt.
2. Use the provider's structured-output/JSON-schema mode.
3. **Always** validate in code (Pydantic) and retry with the error message.

Tools get their own full section next.

---

## 3b. Tools: function calling and the tool catalogue

Lessons 07 (how tool calling works) and 08 (the six kinds of tools).
Read them right after lesson 03. They're numbered 07/08 only because
they were added later.

### What a tool is

A model can only write text. A **tool** is a function *you* describe to
it. The model writes a request to call it, **your code** runs it, and
the result goes back into the context. The model never executes anything.

```
 ┌────────────────────────── one tool-call round trip ──────────────────────────┐
 │                                                                              │
 │  1. you send   : messages + TOOL DEFINITIONS                                 │
 │  2. model writes: tool_call {id, name: "search_orders", arguments: {...}}    │
 │                   stop_reason = tool_use / tool_calls                        │
 │  3. YOUR CODE  : ┌──────────┐   ┌───────────┐   ┌─────┐   ┌──────────────┐   │
 │                  │ validate │ → │ permission│ → │ run │ → │ shape result │   │
 │                  │ args     │   │ gate      │   │     │   │ (small!)     │   │
 │                  └────┬─────┘   └─────┬─────┘   └──┬──┘   └──────┬───────┘   │
 │                       └── any failure becomes an ERROR RESULT, not a crash ──┘
 │  4. you send   : tool result, linked by the call id                          │
 │  5. model      : answers, or asks for another tool  (loop = an AGENT)        │
 └──────────────────────────────────────────────────────────────────────────────┘
```

### The tool definition: four parts

```
 ┌──────────────── Tool definition ────────────────┐
 │ 1. Name and description  when to use it, what   │ ← the model's ONLY documentation
 │                          it returns, what NOT   │
 │ 2. Input / output schema JSON Schema for args;  │ ← input is sent to the API;
 │                          shape of the result    │   output schema native in MCP
 │ 3. Error handling        error codes + how to   │ ← folded into the description
 │                          recover from each      │
 │ 4. Usage examples        concrete calls to copy │ ← folded into the description
 └─────────────────────────────────────────────────┘
```

Don't hand-write schemas. Generate them from typed functions and
docstrings (lesson 07 shows the mechanism in ~30 lines; in practice use
Pydantic, LangChain `@tool`, FastMCP `@mcp.tool`, or your SDK's helper).
The same definition in each wire format:

| | Wrapper | Schema field |
|---|---|---|
| OpenAI | `{"type": "function", "function": {name, description, parameters}}` | `parameters` |
| Anthropic | `{name, description, input_schema}` | `input_schema` |
| MCP | `{name, description, inputSchema, outputSchema?}` | `inputSchema` |

Definitions are context too: the 3 tools in lesson 07 cost ~330 input
tokens **on every call**.

### Measured (lesson 07)

| What | Result |
|---|---|
| Model sends wrong arg name + wrong type | Validation returns `missing 'customer_email'`, `unknown 'email'`, `'limit' must be integer`; the model **fixes the call** on the next turn |
| Side-effect tool (`cancel_order`) | Permission gate asks the user before running |
| 3 weather lookups in one turn | 0.9s one by one → **0.3s** concurrently |
| Vague vs clear tool names/descriptions | **4/8 vs 8/8** requests routed to the right tool |
| Return everything vs a shaped result | **13,093 → 88 tokens**, and it stays in context for the rest of the chat |

### tool_choice

| Mode | OpenAI | Anthropic | Use for |
|---|---|---|---|
| Model decides | `"auto"` | `{"type": "auto"}` | Almost always |
| Never call | `"none"` | `{"type": "none"}` | A summarize-only turn |
| Must call some tool | `"required"` | `{"type": "any"}` | Pipelines that always need a lookup |
| Must call tool X | `{"type": "function", "function": {"name": "X"}}` | `{"type": "tool", "name": "X"}` | Rarely; use structured outputs for JSON |
| One call per turn | `parallel_tool_calls=False` | `disable_parallel_tool_use: true` | Strictly ordered steps |

Some of the newest reasoning models reject forced tool choice (`required`/`any`/specific). Use `auto` and say which tool to use in the prompt.

### Tool design rules

- **Name** = `verb_noun`, unambiguous: `search_orders`, not `orders` or `tool_a`.
- **Description** = when to use it, what it returns, when *not* to use it, and how it chains ("call `search_orders` first to get the id").
- **Parameters**: describe each one with an example and units; use enums wherever the values are known.
- **Errors** say how to *fix* the call; return them as results with `is_error`.
- **Results**: filter, paginate (`limit` + `count`), return only needed fields plus the ids the next tool takes.
- **Fewer, distinct tools** beat many overlapping ones.
- **Tool descriptions are prompts**: version them and evaluate them.

### The tool catalogue: six kinds of tools (lesson 08)

```
                          Tool definition (name, schemas, errors, examples)
                                             │
   ┌──────────────┬──────────────┬───────────┼────────────┬──────────────┬──────────────┐
   ▼              ▼              ▼           ▼            ▼              ▼              │
 Web search   Code exec /    Database     API          Email /        File system       │
              REPL           queries      requests     Slack / SMS    access            │
   └──────────────┴──────────────┴───────────┬────────────┴──────────────┘              │
                                             ▼                                          │
                          Model Context Protocol (MCP): one server per system ◄─────────┘
```

| Tool type | Typical calls | Main risk | Must-have guardrail | Demo in lesson 08 |
|---|---|---|---|---|
| **Web search** | search, fetch page | Injected instructions in pages | Treat as data, cite URLs, domain filters | A spam page saying "IGNORE ALL PREVIOUS INSTRUCTIONS" gets flagged; `allowed_domains` drops it |
| **Code execution / REPL** | run Python/shell | Arbitrary code | Real sandbox (container, no network), timeout, output cap | Primes sum = 76127 exact; `1/0` returns a traceback; `while True` killed at the timeout |
| **Database queries** | narrow queries, text-to-SQL | Data leak, destructive SQL | Parameterized queries, read-only DB user, row-level security | `open' OR '1'='1` returns nothing; `DELETE` refused; unknown table → error the model can fix |
| **API requests** | GET/POST to services | SSRF, leaked secrets | Host allowlist, secrets added server-side, trimmed responses | `169.254.169.254` (cloud metadata) blocked; 503 → `retryable: true`; response 197 → 27 tokens |
| **Email / Slack / SMS** | draft, send, post | Irreversible, spam | Draft → confirm → send, idempotency key, recipient rules | Retry after send → `already_sent`; external recipient refused; 1 message delivered |
| **File system access** | list, read, write | Path escape, overwrites | Resolve path *then* check it's inside the root; write gate | `../../.env` and `~/.ssh/id_rsa` blocked |

**Narrow tool vs flexible tool:** `orders_by_status(status)` is safe by
construction but only answers one question. `run_sql(query)` answers
anything, but needs a read-only user, row caps, timeouts and row-level
security. Start narrow for anything user-facing.

### Who runs the tool?

| | Client tools | Server tools |
|---|---|---|
| Who executes | **Your code** (everything in lessons 07/08) | **The provider** (typically web search, web fetch, code execution) |
| Round trip | Model → you → model | Inside one API response |
| Control | Full | Limited to the provider's options |

### Where MCP fits

```
  your agent (MCP client) ──► MCP server "files"   → list_files, read_file
                          ├──► MCP server "db"      → run_sql
                          ├──► MCP server "slack"   → send_message
                          └──► MCP server "search"  → web_search
```

MCP doesn't change anything on the model's side. The client fetches
tool definitions from each server at runtime, sends them to the model
exactly as above, and forwards the model's calls to the right server.
Write a tool once as an MCP server and any MCP client (your agent,
Claude Code, an IDE) can use it. **The guardrails belong inside the
server.** Build servers: `learn-mcp/01–09`. Attach them to an agent:
`learn-mini-claude/03`.

| Term | What it is | Where |
|---|---|---|
| Tool call | One request/result round trip | lessons 03, 07 |
| Agent | A loop of tool calls until the model stops asking | `learn-mini-claude/01–05` |
| MCP | A protocol for serving tools from a separate process, reusable by any client | `learn-mcp/` |
| Subagent | An agent exposed as a tool to another agent | `learn-mini-claude/06` |

### Tool calling in code: a complete loop

**This repo's helper (LangChain + Azure OpenAI):**

```python
import json
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from llm_helper import get_llm

@tool
def get_weather(city: str) -> dict:
    """Get the current weather for a city."""
    return {"city": city, "temp_c": 24}

llm = get_llm(model="gpt-4-1", temperature=0).bind_tools([get_weather])
messages = [HumanMessage("What's the weather in Rome?")]
ai = await llm.ainvoke(messages)
messages.append(ai)
for call in ai.tool_calls:                               # [{"name", "args", "id"}]
    result = get_weather.invoke(call["args"])
    messages.append(ToolMessage(content=json.dumps(result), tool_call_id=call["id"]))
final = await llm.ainvoke(messages)
print(final.content)
```

**OpenAI SDK:**

```python
import json
from openai import OpenAI
client = OpenAI()
TOOLS = {"get_weather": lambda city: {"city": city, "temp_c": 24}}
tools = [{"type": "function", "function": {
    "name": "get_weather", "description": "Get the current weather for a city.",
    "parameters": {"type": "object", "properties": {"city": {"type": "string"}},
                   "required": ["city"]}}}]

messages = [{"role": "user", "content": "What's the weather in Rome?"}]
while True:
    resp = client.chat.completions.create(model="gpt-4.1", messages=messages, tools=tools)
    msg = resp.choices[0].message
    messages.append(msg)
    if not msg.tool_calls:
        break
    for call in msg.tool_calls:
        args = json.loads(call.function.arguments)       # arguments is a JSON STRING
        result = TOOLS[call.function.name](**args)
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
print(msg.content)
```

**Anthropic SDK:**

```python
import json
import anthropic
client = anthropic.Anthropic()
TOOLS = {"get_weather": lambda city: {"city": city, "temp_c": 24}}
tools = [{"name": "get_weather", "description": "Get the current weather for a city.",
          "input_schema": {"type": "object", "properties": {"city": {"type": "string"}},
                           "required": ["city"]}}]

messages = [{"role": "user", "content": "What's the weather in Rome?"}]
while True:
    resp = client.messages.create(model="claude-opus-5", max_tokens=16000,
                                  tools=tools, messages=messages)
    messages.append({"role": "assistant", "content": resp.content})   # keep ALL blocks
    if resp.stop_reason != "tool_use":
        break
    results = [{"type": "tool_result", "tool_use_id": b.id,
                "content": json.dumps(TOOLS[b.name](**b.input))}      # input is already a dict
               for b in resp.content if b.type == "tool_use"]
    messages.append({"role": "user", "content": results})             # ALL results, ONE message
print(next(b.text for b in resp.content if b.type == "text"))
```

In production, add everything from lesson 07 to these loops:
argument validation, a permission gate for side effects, errors
returned as results, a cap on iterations, and logging.

---

## 4. No-confusion FAQ

**Is `max_tokens` the same as the context window?**
No. The context window is the total the model can handle per call
(input + output). `max_tokens` is *your* cap on the **output** only.

**Does temperature 0 make answers correct?**
No. It makes them the *most likely*. A model that's confidently wrong
is wrong every time at T=0.

**Does temperature 0 guarantee identical output?**
In theory yes. On real APIs it's close but not guaranteed (hardware and
batching effects). Use `seed` for best-effort reproducibility.

**Should I set both temperature and top_p?**
Usually no. Tune one and leave the other at its default. Some models
reject both, or reject sampling parameters entirely.

**Why did my JSON come back broken?**
Most often `stop_reason` was `max_tokens`/`length` and it was cut off.
Raise `max_tokens`, ask for shorter output, or use structured outputs.

**Why does the chatbot "forget" things?**
It never remembered them. Your app resends history. If history was
trimmed or summarized, or never saved, the model can't see it.

**Why does it make things up?**
It generates plausible tokens. Nothing checks them against reality
unless you put the facts in the context (RAG, tools) and tell it to
answer only from them.

**Can I teach it my company's docs by chatting with it?**
Not permanently. Put the docs in the context per request (RAG). Fine-tuning
is a poor way to add facts (section 7).

**What's the difference between a system prompt and a user message?**
Both are tokens in one stream. Models are trained to give the system
prompt more authority, so put rules there. It's not a security
boundary, though; enforce security in code.

**What's "reasoning"/"thinking" in newer models?**
The model generates hidden tokens working through the problem before
the visible answer. It costs tokens and latency. Control it with the
provider's effort/thinking setting rather than temperature.

**Are prompt caching and response caching the same?**
No. **Prompt caching** is done by the provider: a repeated identical
*prefix* is billed at a discount, and you still get a fresh answer.
**Response caching** is done by you: an identical *request* returns a
stored answer with no LLM call (section 7).

**Agent, workflow, chain: what's the difference?**
In a **chain/workflow**, your code decides the steps. In an **agent**, the
model decides the next step in a loop. Use the simplest one that works.

---

## 5. Context engineering

### What it is

> **Context engineering** is deciding, for every LLM call, *what*
> information goes into the context window, *in what form*, *in what
> order*, and *what stays out*.

```
 ┌─────────────────────────── context engineering ────────────────────────────┐
 │                                                                            │
 │   ┌──────────────── prompt engineering ─────────────────┐                  │
 │   │ wording of instructions, examples, output format    │   retrieval      │
 │   └──────────────────────────────────────────────────────┘   memory        │
 │   tool selection · history compaction · tool-output trimming · ordering    │
 │   caching · budgets · isolation (subagents) · verifying what went in       │
 └────────────────────────────────────────────────────────────────────────────┘
```

A model can only be as good as its context. Most "the model got it
wrong" bugs are really *the right fact wasn't in the context*, or *it
was buried under noise*.

### What competes for the window

```
  ┌─ STABLE (same every call) ─────────┐   ┌─ VOLATILE (changes per call) ───────────────────┐
  │ system prompt   tool definitions   │   │ memory · retrieved docs · history · tool results │
  │ few-shot examples (if fixed)       │   │ current time · THE QUESTION                      │
  └────────────────────────────────────┘   └──────────────────────────────────────────────────┘
      first → cacheable prefix                 last → the model's attention is on the task
```

### The four strategies

| Strategy | Idea | Examples | Where in this repo |
|---|---|---|---|
| **WRITE** | Save information *outside* the context window | Long-term memory, notes files, scratchpads, `AGENT.md`/`CLAUDE.md` | `learn-mini-claude` (notes MCP server, AGENT.md) |
| **SELECT** | Pull in only what *this* call needs | RAG top-k, relevant memories, tool selection, similar few-shot examples | lesson 04, lesson 05, `learn-ai-advanced/01` |
| **COMPRESS** | Same information, fewer tokens | Summarize old turns (compaction), trim tool output to needed fields | lesson 04 |
| **ISOLATE** | Push noisy sub-tasks into separate contexts | Subagents, parallel workers, sandboxed tool state | `learn-mini-claude/06`, `learn-langgraph/11,13` |

### Measured (lesson 04)

A support question needs 4 facts, which come from the docs, the account
data, an old chat turn, and the question itself. Budget: 600 tokens.

| Context | Tokens | Required facts present |
|---|---|---|
| A) Everything, no limit | 1,141 (over budget) | 4/4, but pays for 10 docs, 12 tools, 36 junk fields |
| B) Truncate, keep start | 600 | **2/4**: lost the question and the account data |
| C) Truncate, keep end | 600 | **3/4**: lost the docs (and the system rules) |
| **D) Engineered** | **353** | **4/4** |

```
 section     raw → final   action
 system       50 →   52    keep (stable)
 tools       173 →   68    SELECT 4 of 12
 memory       17 →    9    SELECT 1 of 3
 docs        247 →   96    SELECT top-2 of 10
 history     164 →   66    COMPRESS: summary + last 4 turns
 account     410 →   33    COMPRESS: 4 of 40 fields
 question     28 →   30    keep, placed LAST
 TOTAL      1089 →  353    (32% of raw)
```

### Order matters

**For cost (prompt caching):** providers discount the longest identical
*prefix*. One changed byte early on invalidates everything after it.

| Same content, different order | Cacheable share of the next request |
|---|---|
| Timestamp + question first, rules after | **2%** |
| Rules + tools first, timestamp + question last | **95%** |

Keep the stable part byte-identical: no timestamps or user names in
the system prompt, and sorted JSON keys. (Trade-off: selecting different
tools per question changes the tool block and breaks the cache. With a
few tools, send them all.)

**For quality:** models attend most reliably to the start and the end
of a long context ("lost in the middle"). Put rules at the start and
the task/question at the end.

### Failure modes

| Failure | What happens | Fix |
|---|---|---|
| **Poisoning** | A wrong fact (hallucination, bad tool result, injected instruction) enters the context and gets reused | Validate tool output; don't save unverified claims to memory; mark untrusted text as data |
| **Distraction** | So much material that the model follows noise | SELECT and COMPRESS. More context is not better context |
| **Confusion** | Many similar tools/docs; the model picks the wrong one | Fewer, clearly distinct tools; tool selection |
| **Clash** | Parts of the context disagree | Date and source every doc; remove superseded info; state precedence |
| **Truncation** | A needed piece fell off, or the answer hit `max_tokens` | Per-section budgets; reserve output tokens; check `stop_reason` |

### Checklist, for every LLM call in your app

- [ ] What facts does the model need for *this* request, and where does each come from?
- [ ] What's in the context that isn't needed? Remove it.
- [ ] Is each section within budget, with output tokens reserved?
- [ ] Is the stable part first and byte-identical across calls?
- [ ] Is the task/question at the end?
- [ ] Is untrusted content (docs, web, tool output) wrapped and treated as data?
- [ ] In long sessions: what gets summarized, and what gets saved to memory?
- [ ] For big sub-tasks: should a subagent do it in its own context?
- [ ] Can you **log the exact context sent**, to debug a bad answer? (`learn-ai-advanced/03`)

---

## 6. Prompt engineering

The instruction-writing part of context engineering (lesson 05).

**Anatomy of a good prompt:**

```
 ROLE        You are a support triage assistant for Acme Cloud.
 TASK        Summarize the customer email for the on-call engineer.
 CONTEXT     They read it on a phone, in under 10 seconds.         <- the WHY drives good choices
 DATA        <email> ... </email>                                  <- delimiters: data, not instructions
 FORMAT      SEVERITY: low|medium|high / ONE-LINE: ≤15 words / ACTION: ...
 EDGE CASES  If there's no problem, reply SEVERITY: low, ONE-LINE: no issue reported.
```

The test: could a smart new colleague do the task exactly right from
**only** this text? If they'd need to ask, put the answer in the prompt.

| Technique | Measured / key point (lesson 05) |
|---|---|
| **Few-shot examples** | Choice matters: similar examples **8/8** correct vs random 5/8 vs "first 3" 2/8 |
| **Delimiters / XML tags** | Separate data from instructions; a partial defence against injection |
| **Reasoning first** (CoT) | Let the model think before the answer; parse only `<answer>`. With reasoning models, use the effort setting instead |
| **Self-consistency** | Sample N at T>0 and take the majority. One answer 60% right → 3 votes **73.9%**, 5 votes **85.4%**, 9 votes **95.5%**. Costs N× |
| **Prompt chaining** | Split one big prompt into small steps; use code for anything deterministic |
| **Prompts as code** | Version control, one prompt per file, an eval set run on every change |

**Anti-patterns:** vague adjectives ("be concise"), only saying what
*not* to do, ALL-CAPS threats, contradictions, asking the LLM to do
maths or lookups, and editing a prompt without re-running evals.

---

## 7. Production engineering

The engineering around the call (lesson 06).

| Topic | Key result / rule |
|---|---|
| **Latency** | `total = TTFT + output_tokens / tokens_per_sec`. An 800-token answer takes 10.6s; streamed, the first text shows at 0.6s. Output length dominates, so "max 3 sentences" is a latency fix |
| **Model routing** | 10k requests, 20% hard: all-large **$175 / 96.7%**, routed small↔large **$42 / 94.2%**, all-small $9 / 87.1%. Judge cost per *solved* task |
| **Response caching** | Exact-match cache with normalized keys avoided **65%** of calls on FAQ-heavy traffic. Only for user-independent, low-temperature answers, with a TTL |
| **Reliability** | 8% failure rate: no retry 91.9% → 2 retries 99.97% → + fallback model 99.995%. Retry only 429/5xx/timeouts, with backoff + jitter; make tools idempotent |
| **Batch** | Offline work through batch APIs costs about **50% less**. Cap real-time concurrency with a semaphore |
| **Security** | No secrets in prompts; redact PII; least-privilege tools; validate output before executing/rendering; per-user spend caps |

### Prompting vs RAG vs tools vs fine-tuning

```
 What's actually wrong?
  ├─ doesn't follow format / tone / steps   → PROMPT ENGINEERING (then fine-tune only at high volume)
  ├─ doesn't KNOW the facts                 → RAG / tools   (fine-tuning is a poor way to add facts)
  ├─ must take actions or use live data     → TOOLS / agents
  ├─ works, but too slow/costly at scale    → smaller model + better prompt → then fine-tune/distill
  └─ can't tell if it's working             → EVALS first
```

| Approach | Changes | Cost to try | Update | Good for |
|---|---|---|---|---|
| Prompting | the instructions | minutes | instant | behaviour, format |
| RAG | the context | days | re-index | knowledge, citations |
| Tools | what it can do | days | deploy | live data, actions |
| Fine-tuning | the weights | weeks + data | retrain | narrow, high-volume tasks |

---

## 8. The AI engineer roadmap

An AI engineer builds **reliable products on top of models**. The job
is mostly software engineering plus the skills below, not training
models from scratch. Each stage maps to where this repo teaches it.

```
 STAGE 0  Foundations        Python, async, HTTP APIs, JSON, git, SQL, Docker
    │
 STAGE 1  How LLMs work      tokens, sampling, context window, API anatomy, cost
    │
 STAGE 2  Prompt + context   prompt engineering, structured output, context engineering
    │
 STAGE 3  Knowledge (RAG)    embeddings, chunking, vector search, reranking, grounding
    │
 STAGE 4  Tools + agents     tool calling, agent loop, MCP, orchestration, human-in-the-loop
    │
 STAGE 5  Quality            evals, LLM-as-judge, regression tests, guardrails, injection defence
    │
 STAGE 6  Production         observability, latency, caching, routing, retries, cost, security
    │
 STAGE 7  Ship it            APIs, streaming UIs, deployment, CI/CD, monitoring
```

| Stage | Skill | Where in this repo | Status |
|---|---|---|---|
| 0 | Python, types, async, Pydantic | `python/01–10` | ✅ |
| 0 | HTTP APIs with FastAPI | `fastapi/01–09` | ✅ |
| 0 | Git | `github/` | ✅ |
| 1 | Tokens, next-token prediction, hallucination | **`learn-llm-fundamentals/01`** | ✅ |
| 1 | Temperature, top_p, top_k, penalties, stop, max_tokens | **`learn-llm-fundamentals/02`** | ✅ |
| 1 | API anatomy, roles, statelessness, cost | **`learn-llm-fundamentals/03`** | ✅ |
| 1 | Tool calling: definitions, validation, tool_choice, parallel calls, design | **`learn-llm-fundamentals/07`** | ✅ |
| 1 | Tool types: web search, code exec, DB, APIs, messaging, files + guardrails | **`learn-llm-fundamentals/08`** | ✅ |
| 2 | Context engineering | **`learn-llm-fundamentals/04`** | ✅ |
| 2 | Prompt engineering, few-shot, CoT, self-consistency | **`learn-llm-fundamentals/05`** | ✅ |
| 2 | Structured output + validation | `learn-llm-fundamentals/03`, `learn-ai-advanced/04` | ✅ |
| 3 | Embeddings, chunking, vector store, grounding | `learn-ai-advanced/01` | ✅ |
| 4 | Agent loop, tools, sandbox, permissions | `learn-mini-claude/01–05` | ✅ |
| 4 | LLM vs agent vs subagent | `learn-mini-claude/06` | ✅ |
| 4 | MCP servers, clients, multi-server | `learn-mcp/01–16` | ✅ |
| 4 | Graph orchestration, checkpoints, HITL, subgraphs | `learn-langgraph/01–13` | ✅ |
| 4 | Agent UIs, generative UI | `learn-copilotkit/` | ✅ |
| 5 | Evals, golden datasets, LLM-as-judge | `learn-ai-advanced/02` | ✅ |
| 5 | Guardrails, PII, prompt injection | `learn-ai-advanced/04` | ✅ |
| 6 | Tracing, token/cost tracking | `learn-ai-advanced/03` | ✅ |
| 6 | Latency, routing, response caching, batch, fine-tune decision | **`learn-llm-fundamentals/06`** | ✅ |
| 6 | Retries, error handling | `learn-langgraph/12`, `learn-mcp/06` | ✅ |
| 6 | Streaming | `learn-langgraph/10`, `learn-mcp` | ✅ |
| 7 | Deploy to AWS (Lambda, Fargate, IaC) | `project-book-store/`, `aws/` | ✅ |
| 7 | System design for scale | `system-design/` | ✅ |

**Not in this repo yet: learn these next.** The full checklist, with
subtopics and progress tracking, is in
[`AI_ENGINEER_LEARNING_BACKLOG.md`](../AI_ENGINEER_LEARNING_BACKLOG.md).

| Topic | Why it matters | Start with |
|---|---|---|
| Production vector databases | Scaling RAG past an in-memory list | pgvector, OpenSearch, or a managed vector DB; hybrid (keyword + vector) search; rerankers |
| Multimodal | Images, PDFs, audio in and out | Your provider's vision/document input docs |
| Fine-tuning hands-on | Narrow, high-volume tasks; distillation | Provider fine-tuning guides; LoRA with Hugging Face `peft` for open models |
| Open-weight / local models | Privacy, cost, offline | Ollama or vLLM; compare against your eval set |
| Transformer internals | Intuition for attention, context limits | Karpathy's *Let's build GPT* and 3Blue1Brown's transformer videos |

**Projects that prove the skills** (build them in order):

1. **CLI chatbot** with history, a token/cost counter and a `/temperature` command (stages 1–2)
2. **Docs Q&A (RAG)** over your team's docs with citations and "I don't know" behaviour, plus a 20-question eval set (stages 3, 5)
3. **Tool-using agent** that calls 3 real internal APIs through MCP, with a permission gate and tracing (stages 4, 6)
4. **Ship it:** a FastAPI backend, streaming UI, deployed on AWS with dashboards for cost, latency and eval score (stage 7)

---

## 9. Glossary

| Term | Meaning | Lesson |
|---|---|---|
| **Token** | A chunk of text (word, sub-word, punctuation) with an integer ID | 01 |
| **Vocabulary** | Every token a model knows (~100k–200k) | 01 |
| **Logit** | The raw score a model gives each possible next token | 02 |
| **Softmax** | Turns logits into probabilities summing to 1 | 02 |
| **Temperature** | Divides logits before softmax; lower = sharper, higher = flatter, 0 = greedy | 02 |
| **top_k** | Keep only the k most likely tokens | 02 |
| **top_p / nucleus** | Keep the smallest set of tokens whose probability sums to p | 02 |
| **Greedy decoding** | Always pick the most likely token | 02 |
| **Frequency / presence penalty** | Lower logits of already-used tokens to reduce repetition | 02 |
| **max_tokens** | Cap on output tokens for one call | 02 |
| **Stop sequence** | A string that ends generation when produced | 02 |
| **stop_reason / finish_reason** | Why generation ended: done, cap hit, tool call, stop string, refusal | 03 |
| **Context window** | Max tokens (input + output) the model handles per call | 01, 04 |
| **Chat template** | Model-specific format that flattens role messages into one token stream | 03 |
| **System prompt** | Operator instructions; persona, rules, format | 03 |
| **Stateless** | The API keeps nothing between calls; you resend history | 03 |
| **Tool call** | Model output shaped as `{name, arguments}` that your code executes | 03 |
| **Structured output** | Constraining/validating output to a JSON schema | 03 |
| **Tool definition** | Name, description, input/output schema, errors, examples: all the model knows about a tool | 07 |
| **tool_choice** | Whether the model may, must, or must not call tools (or a specific one) | 07 |
| **Parallel tool calls** | Several tool calls in one model turn; run them concurrently, return results together | 07 |
| **Client vs server tools** | Tools your code runs vs tools the provider runs for you (e.g. web search) | 08 |
| **Text-to-SQL** | A tool that lets the model write SQL; needs read-only access and row limits | 08 |
| **SSRF** | Tricking a server into fetching internal URLs; blocked by a host allowlist | 08 |
| **Idempotency key** | An id that makes a retried side effect (send, charge) happen only once | 08 |
| **Hallucination** | Fluent, plausible, false output | 01 |
| **Knowledge cutoff** | The date the training data ends | 01 |
| **Context engineering** | Choosing what goes into the context, in what form and order | 04 |
| **RAG** | Retrieval-augmented generation: fetch relevant docs into the context | 04 |
| **Compaction** | Replacing old conversation turns with a summary | 04 |
| **Memory** | Facts saved outside the context and re-injected when relevant | 04 |
| **Prompt caching** | Provider discount for a repeated identical prompt prefix | 04 |
| **Lost in the middle** | Models use information at the start/end of long contexts more reliably than the middle | 04 |
| **Few-shot** | Including input→output examples in the prompt | 05 |
| **Chain-of-thought** | Asking for reasoning before the final answer | 05 |
| **Self-consistency** | Majority vote over several sampled answers | 05 |
| **Prompt chaining** | Splitting a task into sequential prompts | 05 |
| **TTFT** | Time to first token | 06 |
| **Model routing** | Choosing a model per request (e.g. by difficulty) | 06 |
| **Response caching** | Returning a stored answer for an identical request | 06 |
| **Fallback** | An alternate model/provider when the primary fails | 06 |
| **Fine-tuning** | Further training a model's weights on your examples | 06 |
| **Reasoning / thinking model** | A model that generates internal reasoning tokens before answering | 02, 05 |
| **Effort** | Setting on reasoning models controlling how much they think | 02 |
