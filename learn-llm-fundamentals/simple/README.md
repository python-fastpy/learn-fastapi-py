# LLM Fundamentals — Simple Version

Short versions of the lessons in the parent folder. Each one has about 100 lines of code,
and the rest of the file is diagrams. Every file follows the same pattern:

1. **IN ONE LINE**: the idea in one sentence
2. **REAL USE CASE**: where it sits in a FastAPI app (Browser → FastAPI → LLM)
3. **HOW IT WORKS**: a pipeline diagram of the idea
4. **A REAL RUN**: a table that traces one run, step by step, with the numbers the script prints
5. **WHAT AN ENGINEER MUST KNOW**: 3–5 points
6. **Small code in STEPs**: a diagram above each function shows what goes in, what happens and what comes out

The numbers in the diagrams are the same as the script output, and the output is the same
on every run. So run the file and read the diagram next to the output.

**Videos:** [VIDEOS.md](VIDEOS.md) lists a video or visual tool for each lesson, plus a weekly plan.

**Hands-on with a real model:** [ollama/](ollama/README.md) teaches every concept quickly with a free
open-source model (llama3.2) running on your PC. No API key needed.

The full, detailed lessons are still in the parent folder. Open them when you want more depth.

## The big picture: how one chat request works

```
User types a message in your app
        │
        ▼
┌──────────────── YOUR FASTAPI CODE ────────────────┐
│ build prompt: system + docs + history + message   │  04 context, 05 prompts
│ (RAG: search your docs, add the best chunks)      │  10 RAG
│ count tokens, check the limits                    │  01b tokens, 06 production
└────────────────────────┬──────────────────────────┘
                         │ messages[] + tools[] + settings   03 API
                         ▼
┌──────────────── THE LLM ──────────────────────────┐
│ text → tokens → predict next token → loop         │  01, 01b, 12
│ "pick one" uses temperature / top_p               │  02 sampling
└────────────────────────┬──────────────────────────┘
                         │ answer OR "please call tool X"
                         ▼
┌──────────────── YOUR FASTAPI CODE ────────────────┐
│ tool call? → run the tool → send the result back  │  07, 08 tools
│ repeat many steps until the goal is done          │  09 agents
│ check the answer is safe and correct              │  11 evals, guardrails
└───────────────────────────────────────────────────┘
```

## Order to read

| # | File | Question it answers |
|---|------|---------------------|
| 01 | `01_what_is_an_llm.py` | What does an LLM actually compute? |
| 01b | `01b_extra_how_bytes_work.py` | How does text become numbers? |
| 01b | `01b_tokens_in_depth.py` | What is a token, and why do I pay per token? |
| 02 | `02_sampling_temperature_top_p.py` | Why does the same prompt give different answers? |
| 03 | `03_chat_api_anatomy.py` | What is inside an API request and response? |
| 04 | `04_context_engineering.py` | What should I put in the prompt? |
| 05 | `05_prompt_engineering.py` | How do I write instructions that work? |
| 06 | `06_production_llm_engineering.py` | Retries, timeouts, cost, caching in real apps |
| 07 | `07_tool_calling.py` | How does the model "use" a function? |
| 08 | `08_tool_types_catalogue.py` | What kinds of tools exist? |
| 09 | `09_agents.py` | What is an agent? (a tool loop with a goal) |
| 10 | `10_rag_and_embeddings.py` | How does the model answer from MY documents? |
| 11 | `11_evals_and_guardrails.py` | How do I test that answers are good and safe? |
| 12 | `12_inside_the_transformer.py` | How does attention work inside the model? |
| 13 | `13_reasoning_and_structured_output.py` | What do "thinking" tokens cost, and how do I get valid JSON? |
| 14 | `14_fine_tuning.py` | When and how do I train a model on my own data? |
| 15 | `15_run_open_models_locally.py` | How much memory does a model need, and how do I run one on my PC? (includes 15b) |
| 16 | `16_own_model_with_your_context.py` | Should I train a model or give it my documents? |
| 17 | `17_deploy_your_model_free.py` | How do I put my model behind a safe API for free? |

Run any lesson from the `learn-llm-fundamentals` folder:

```
uv run python simple/01_what_is_an_llm.py
```
