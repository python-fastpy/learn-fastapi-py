# Hands-on with a free open-source model (Ollama)

Learn every LLM concept quickly, using a **real model running on your own PC**.
It's free: no account, no API key, no cost per call. Each lesson is short (about 50–100 lines)
and teaches one idea. You don't need deep details about how the model works inside.

```
your Python ──HTTP JSON──▶ Ollama (localhost:11434) ──▶ llama3.2 (open-source, ~2 GB)
            ◀── answer + token counts ──────────────────┘
```

This is the same request/response shape as paid APIs (OpenAI, Anthropic), so what you learn
here carries over directly.

## Setup (once, about 10 minutes)

1. Install Ollama from https://ollama.com/download
2. Download the two models:
   ```
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```
3. From the `learn-llm-fundamentals` folder, check that everything works:
   ```
   uv run python simple/ollama/00_setup_check.py
   ```

Hardware: llama3.2 (3B) runs on a normal laptop CPU with 8 GB RAM. A GPU makes it faster,
but you don't need one.

**Cost: free.** Running models on your own PC is free and unlimited, with no account and no API key.
Your prompts never leave your PC.

## The lessons: one concept each

**Part 1: how an LLM works**

| # | File | Concept | What you see with the real model |
|---|------|---------|-----------------------------------|
| 00 | `00_setup_check.py` | Setup | Ollama running, models downloaded, first answer |
| 01 | `01_next_token.py` | **Next-token prediction** | The model's top 5 choices for every token it writes |
| 01b | `01b_inside_the_llm.py` | **Inside the model** | Real size (28 layers, 128k vocab), the raw chat template, the loop run by hand one token per call |
| 02 | `02_tokens_and_cost.py` | **Tokens and cost** | Real token counts: English vs Hindi vs JSON vs typos |
| 03 | `03_temperature.py` | **Temperature, seed** | Same prompt at temperature 0 / 1 / 1.8: same vs varied answers |
| 04 | `04_chat_messages.py` | **Roles, no memory, done_reason** | The model forgets your name; input grows each turn; an answer cut off by the limit |
| 05 | `05_context_window.py` | **Context window** | A small window cuts off the start, so the model "forgets" a code; a summary fixes it |
| 06 | `06_streaming.py` | **Streaming** | Words appear live; time to first token |

**Part 2: getting good answers**

| # | File | Concept | What you see |
|---|------|---------|--------------|
| 07 | `07_prompt_and_context.py` | **Prompts, hallucination, injection, few-shot** | A guess without facts vs the right answer with facts; examples fix the format |
| 08 | `08_reasoning.py` | **Chain of thought, thinking models** | A direct guess vs step-by-step; `message.thinking` from a thinking model |
| 09 | `09_structured_output.py` | **JSON schema + validation** | Valid JSON, checked, retried on error |

**Part 3: tools, agents and MCP**

| # | File | Concept | What you see |
|---|------|---------|--------------|
| 10 | `10_tool_calling.py` | **Tool calling** | The model asks for `get_weather("Paris")`, your code runs it |
| 11 | `11_agent.py` | **Agents** | find customer → get orders → refund, chained step by step |
| 12 | `12_mcp_server.py` | **MCP server** | Your tools served over the MCP standard (JSON-RPC), usable from Claude Desktop / VS Code |
| 13 | `13_mcp_client.py` | **MCP client** | Your app discovers the server's tools and lets llama3.2 use them; every message printed |

**Part 4: your own data (RAG)**

| # | File | Concept | What you see |
|---|------|---------|--------------|
| 14 | `14_embeddings_and_rag.py` | **Embeddings + RAG basics** | "money back" finds the "refunds" doc by meaning |
| 15 | `15_rag_pipeline.py` | **Full RAG pipeline** | Chunking, a saved index, citations like [c3], "I don't know", a retrieval hit rate |

**Part 5: production**

| # | File | Concept | What you see |
|---|------|---------|--------------|
| 16 | `16_evals_and_guardrails.py` | **Evals + guardrails** | Prompt v1 vs v2 scored on a test set; injection blocked |
| 17 | `17_production.py` | **Timeouts, retries, fallback, cache, logging** | A broken model falls back; a cache hit costs 0 tokens; per-request token logs |
| 18 | `18_custom_model_and_finetuning.py` | **Custom model vs fine-tuning** | A model with baked-in rules; when fine-tuning is worth it |
| 19 | `19_fastapi_app.py` | **Everything together** | A real FastAPI `/ask` endpoint: guard → RAG → prompt → model → JSON |

Run any lesson:
```
uv run python simple/ollama/01_next_token.py
```

Run the final app (fastapi and uvicorn are added just for this command):
```
uv run --with fastapi --with uvicorn uvicorn 19_fastapi_app:app --app-dir simple/ollama --port 8019
```
Then open http://localhost:8019/docs and try `/ask`.

Optional, for lesson 08 step 3: `ollama pull qwen3:1.7b` (a small thinking model, about 1.4 GB).

## Concept checklist

When you finish, you should be able to explain each of these in one sentence:

- [ ] Token, tokenizer, context window, `num_ctx` (01, 02, 05)
- [ ] Next-token prediction, logprobs, generation loop (01)
- [ ] Temperature, top_p, seed (03)
- [ ] Roles (system / user / assistant / tool), stateless API, `done_reason` (04)
- [ ] Streaming and time to first token (06)
- [ ] Prompt engineering, few-shot, prompt injection, hallucination (07)
- [ ] Chain of thought and thinking models (08)
- [ ] Structured output and validation (09)
- [ ] Tool calling, agents, step limits (10, 11)
- [ ] MCP: server, client, tools vs resources, JSON-RPC (12, 13)
- [ ] Embeddings, cosine similarity, chunking, vector index, RAG, citations (14, 15)
- [ ] Evals, guardrails (16)
- [ ] Timeouts, retries, fallback, caching, cost logging (17)
- [ ] Prompt vs RAG vs fine-tuning (18)
- [ ] Putting it all behind a FastAPI endpoint (19)

## How this folder fits with the others

| Folder | Use it for |
|--------|------------|
| `simple/ollama/` (here) | **Quick and hands-on**: see each concept happen with a real model |
| `simple/` | **How it works**: small pure-Python versions with detailed diagrams, no model needed |
| parent folder | **In depth**: every detail and edge case |

Each lesson here names its matching `simple/` lesson in its first lines ("details: simple/07").

## Good to know

- **Answers vary by model.** A small 3B model sometimes makes mistakes, especially in agents
  and injection tests. That's useful: you see the real failure modes. Try a bigger model by
  changing `CHAT_MODEL` at the top of a lesson file (for example `qwen2.5:7b` or `llama3.1:8b`).
- **The first call is slow** (about 5–20 s) while the model loads into memory. Later calls are fast.
- **No helper module.** Each lesson calls Ollama directly with `httpx`, so you see the
  raw JSON request and response in every file.

## Same idea, different names: Ollama vs other APIs

The concepts are the same everywhere; only the field names change. Each lesson also notes
these next to the first place a name is used.

**Request settings**

| Ollama | OpenAI | Anthropic | Hugging Face `transformers` |
|---|---|---|---|
| `POST /api/chat` | `POST /v1/chat/completions` (or `/v1/responses`) | `POST /v1/messages` | `model.generate()` |
| `"options": {...}` wrapper | settings at top level | settings at top level | arguments to `generate()` |
| `num_predict` (max output tokens) | `max_tokens` / `max_completion_tokens` | `max_tokens` (required) | `max_new_tokens` |
| `num_ctx` (context window) | fixed per model | fixed per model | model config (`max_position_embeddings`) |
| `temperature` | `temperature` (0–2) | `temperature` (0–1) | `temperature` |
| `top_p` / `top_k` | `top_p` only | `top_p`, `top_k` | `top_p`, `top_k` |
| `seed` | `seed` (best effort) | – | `set_seed()` |
| `logprobs`, `top_logprobs` | `logprobs`, `top_logprobs` | – | `output_scores=True` |
| `"stream": true` (one JSON per line) | `"stream": true` (SSE `data:` lines) | `"stream": true` (SSE events) | `TextStreamer` |
| `"think": true` | `reasoning_effort` | `thinking: {"type": "enabled", "budget_tokens": N}` | – |
| `format: <JSON schema>` | `response_format: {"type": "json_schema", ...}` | structured outputs / tool `input_schema` | – |
| `tools: [{"type": "function", ...}]` | same shape | `tools: [{"name", "description", "input_schema"}]` | – |
| `{"role": "system", ...}` message | same | top-level `"system"` field | in the chat template |
| `/api/generate` + `"raw": true` | legacy `/v1/completions` | – | `generate()` on raw tokens |
| `POST /api/embed` | `POST /v1/embeddings` | – (Voyage AI) | `sentence-transformers` `encode()` |
| `GET /api/tags` | `GET /v1/models` | `GET /v1/models` | – |
| `keep_alive`, `/api/create`, `/api/show` | – (managed for you) | – | `config.json` (for `/api/show`) |

**Response fields**

| Ollama | OpenAI | Anthropic |
|---|---|---|
| `message.content` | `choices[0].message.content` | `content[0].text` |
| `message.tool_calls` | `choices[0].message.tool_calls` | `tool_use` content blocks |
| `done_reason`: `stop` / `length` | `finish_reason`: `stop` / `length` | `stop_reason`: `end_turn` / `max_tokens` |
| `prompt_eval_count` (tokens in) | `usage.prompt_tokens` | `usage.input_tokens` |
| `eval_count` (tokens out) | `usage.completion_tokens` | `usage.output_tokens` |
| `prompt_eval_cached_count` | `usage.prompt_tokens_details.cached_tokens` | `usage.cache_read_input_tokens` |
| `embeddings[i]` | `data[i].embedding` | – |

Ollama also has an OpenAI-compatible endpoint at `http://localhost:11434/v1`, so OpenAI-style
code works against it unchanged.
