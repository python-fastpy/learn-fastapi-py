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

## The lessons: one concept each

| # | File | Concept you learn | What you see with the real model |
|---|------|-------------------|-----------------------------------|
| 00 | `00_setup_check.py` | Setup | Ollama running, models downloaded, first answer |
| 01 | `01_next_token.py` | **Next-token prediction** | The model's top 5 choices for every token it writes |
| 02 | `02_tokens_and_cost.py` | **Tokens and cost** | Real token counts: English vs Hindi vs JSON vs typos |
| 03 | `03_temperature.py` | **Temperature, seed** | Same prompt at temperature 0 / 1 / 1.8: same vs varied answers |
| 04 | `04_chat_messages.py` | **Roles, no memory, done_reason** | The model forgets your name; input tokens grow each turn; an answer cut off by the limit |
| 05 | `05_streaming.py` | **Streaming** | Words appear live; time to first token |
| 06 | `06_prompt_and_context.py` | **Context, hallucination, injection** | A wrong guess without facts, the right answer with facts, "I don't know" |
| 07 | `07_structured_output.py` | **JSON schema + validation** | Valid JSON, checked, retried on error |
| 08 | `08_tool_calling.py` | **Tool calling** | The model asks for `get_weather("Paris")`, your code runs it |
| 09 | `09_agent.py` | **Agents** | find customer → get orders → refund, chained step by step |
| 10 | `10_rag.py` | **RAG + embeddings** | "money back" finds the "refunds" doc by meaning |
| 11 | `11_evals_and_guardrails.py` | **Evals + guardrails** | Prompt v1 vs v2 scored on a test set; injection blocked |
| 12 | `12_fastapi_app.py` | **Everything together** | A real FastAPI `/ask` endpoint: guard → RAG → prompt → model → JSON |

Run any lesson:
```
uv run python simple/ollama/01_next_token.py
```

Run the final app (fastapi and uvicorn are added just for this command):
```
uv run --with fastapi --with uvicorn uvicorn 12_fastapi_app:app --app-dir simple/ollama --port 8012
```
Then open http://localhost:8012/docs and try `/ask`.

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
  changing `CHAT_MODEL` in `ollama_client.py` (for example `qwen2.5:7b` or `llama3.1:8b`).
- **The first call is slow** (about 5–20 s) while the model loads into memory. Later calls are fast.
- **`ollama_client.py`** is the only helper. It's about 50 lines of plain `urllib`, so read it first.
