"""Lesson 15 -- Run an open-source model on your own machine
=============================================================

WHY THIS MATTERS:
  Every other lesson talks to a model through an API someone else runs.
  An OPEN-WEIGHT model is just files you download -- the same weights
  lesson 12 explains -- and run yourself: no API key, no per-token bill,
  nothing leaves your machine. The catch is that YOUR hardware now has to
  hold and run it, so this lesson starts with "will it fit?".

        ┌───────────── download ONCE ─────────────┐
        │  Ollama registry      or   Hugging Face │  (weights + tokenizer)
        └──────────┬────────────────────┬─────────┘
                   ▼                    ▼
           ollama pull qwen2.5     git clone / hf download
                   │                    │
                   ▼                    ▼
          Ollama server :11434    transformers (Python)   <- inference runs
                   │                    │                    on YOUR CPU/GPU
                   ▼                    ▼
           HTTP /api/chat         model.generate(...)
           (like any LLM API)     (lesson 15b)

WHAT YOU'LL LEARN:
  1. Why run locally, and the main tools (Ollama, llama.cpp, LM Studio,
     transformers, vLLM) -- which one to pick
  2. Will it fit? Memory = parameters x bytes per weight, computed for
     0.5B..70B models and compared with YOUR machine's RAM
  3. Quantization: storing weights in 8 or 4 bits -- done by hand, with
     the error it costs measured
  4. PATH A -- Ollama: install, pull, run, then call it over HTTP from
     Python (it runs for real if Ollama is up; otherwise prints the steps)
  5. PATH B -- "clone" a model from Hugging Face: what is inside a model
     repo, git clone vs hf download, then run it with transformers (15b)
  6. Choosing a model + licence checklist, and pointing the earlier
     lessons' code at your local model

Concepts:
  - Open-weight model: weights you can download and run (Llama, Qwen, Gemma, Phi, Mistral)
  - GGUF: llama.cpp / Ollama file format for (usually quantized) weights
  - safetensors: Hugging Face's safe file format for full-precision weights
  - Quantization: fewer bits per weight -> smaller + faster, slightly less accurate
  - tokens/sec: output speed on your hardware (Ollama reports it per call)

PREREQUISITES: Lessons 01-03 and 12. This file is pure Python standard
library. Actually running a model needs ONE of: Ollama (path A) or the
packages in 15b (path B) -- both are optional; without them this lesson
still runs and tells you what to install.

Level: ADVANCED
Run:  uv run python advanced/15_run_open_models_locally.py               (from learn-llm-fundamentals)
      uv run python advanced/15_run_open_models_locally.py --model llama3.2:1b --prompt "Hi"
"""

import argparse
import ctypes
import json
import math
import os
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA = "http://127.0.0.1:11434"
HF_REPO = "Qwen/Qwen2.5-0.5B-Instruct"          # small, Apache-2.0, not gated
HF_DIR = Path(__file__).parent / "models" / "Qwen2.5-0.5B-Instruct"


def header(title: str):
    print(f"\n######## {title} ########\n")


def gb(n_bytes: float) -> str:
    return f"{n_bytes / 1024**3:6.1f} GB"


# ============================================================================
# PART 1: Why local, and which tool
# ============================================================================
#   WHICH TOOL?                                            (all free)
#   ┌──────────────┬──────────────────────────────┬─────────────────────┐
#   │ Ollama       │ one installer, `ollama run`  │ START HERE          │
#   │ LM Studio    │ desktop app with a chat UI   │ no-code exploring   │
#   │ llama.cpp    │ the C++ engine under Ollama  │ max control, CPU    │
#   │ transformers │ Python, full-precision HF    │ research, fine-tune │
#   │ vLLM / TGI   │ high-throughput GPU server   │ serving many users  │
#   └──────────────┴──────────────────────────────┴─────────────────────┘
#   local = privacy + no per-token cost + offline
#   API   = bigger/smarter models + no hardware + someone else's ops

def part1_why_local():
    header("PART 1 -- Why run locally, and which tool")
    rows = [
        ("privacy", "prompts and data never leave the machine", "local"),
        ("cost at volume", "no per-token bill (you pay for hardware/power)", "local"),
        ("offline / air-gapped", "works with no internet", "local"),
        ("best quality", "frontier models are API-only", "API"),
        ("no hardware or ops", "nothing to install, patch or scale", "API"),
        ("long context, speed", "big GPUs behind the API", "API"),
    ]
    print(f"  {'need':<22}{'why':<48}winner")
    for need, why, win in rows:
        print(f"  {need:<22}{why:<48}{win}")
    print("\n  Rule of thumb: prototype on an API, move a task local when privacy,\n"
          "  cost or offline use demands it -- and keep your eval set (lesson 11)\n"
          "  to prove the local model is good enough for THAT task.")


# ============================================================================
# PART 2: Will it fit? Memory math
# ============================================================================
#   MEMORY TO RUN A MODEL  ~=  WEIGHTS  +  KV CACHE  +  overhead
#     weights  = parameters x bits per weight / 8
#     7B model:  FP16 16 bits -> 14 GB │ Q8 8 bits -> 7 GB │ Q4 ~4.5 bits -> ~4 GB
#   ┌──────────── your RAM (or GPU VRAM) ─────────────┐
#   │ OS + apps │ model weights (Q4) │ KV cache │ free │   must not overflow,
#   └───────────┴────────────────────┴──────────┴──────┘   or it swaps = crawls
#   CPU works for <= ~8B at Q4; a GPU is what makes it FAST.

BITS = {"FP16": 16, "Q8_0": 8.5, "Q4_K_M": 4.8}      # GGUF formats incl. scale overhead
# (name, parameters, layers, KV heads, head_dim) -- typical shapes for each size
# (modern models share K/V across query heads = "GQA", which keeps the cache small)
MODELS = [("0.5B", 0.5e9, 24, 2, 64), ("1B", 1.2e9, 16, 8, 64), ("3B", 3.2e9, 28, 8, 128),
          ("8B", 8.0e9, 32, 8, 128), ("14B", 14.8e9, 48, 8, 128), ("32B", 32.8e9, 64, 8, 128),
          ("70B", 70.6e9, 80, 8, 128)]


def machine_ram_bytes() -> int | None:
    """Total physical RAM, standard library only."""
    if sys.platform == "win32":
        class MEMSTAT(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MEMSTAT()
        m.dwLength = ctypes.sizeof(MEMSTAT)
        return m.ullTotalPhys if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)) else None
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        return None


def kv_cache_bytes(layers: int, kv_heads: int, head_dim: int, ctx: int = 4096) -> float:
    """K and V for every layer and every context token, FP16 (lesson 12 part 7)."""
    return 2 * layers * kv_heads * head_dim * ctx * 2


def run_memory(params: float, bits: float, layers: int, kv_heads: int, head_dim: int,
               ctx: int = 4096) -> float:
    """Weights + KV cache for `ctx` tokens + 10% runtime overhead."""
    return (params * bits / 8 + kv_cache_bytes(layers, kv_heads, head_dim, ctx)) * 1.10


def part2_will_it_fit():
    header("PART 2 -- Will it fit? (memory = params x bits / 8, + KV cache)")
    ram = machine_ram_bytes()
    budget = ram * 0.6 if ram else None               # leave room for the OS and apps
    print(f"  this machine: {gb(ram).strip() if ram else 'unknown'} RAM"
          + (f"  -> usable for a model ~{gb(budget).strip()} (60%)" if budget else ""))
    print("  (weights + KV cache for a 4096-token context + 10% overhead)")
    print(f"\n  {'model':<7}" + "".join(f"{k:>12}" for k in BITS) + f"{'KV cache':>11}   fits here (Q4)?")
    for name, p, layers, kvh, hd in MODELS:
        cells = "".join(f"{gb(run_memory(p, b, layers, kvh, hd)):>12}" for b in BITS.values())
        q4 = run_memory(p, BITS["Q4_K_M"], layers, kvh, hd)
        verdict = "-" if not budget else ("yes" if q4 <= budget else "NO")
        print(f"  {name:<7}{cells}{gb(kv_cache_bytes(layers, kvh, hd)):>11}   {verdict}")
    _, p, layers, kvh, hd = MODELS[3]
    print(f"\n  8B at a 32k context: KV cache grows to {gb(kv_cache_bytes(layers, kvh, hd, 32768)).strip()}"
          f" -- long contexts cost memory, not just time.")
    print("\n  Q4 is the usual local default: ~3.3x smaller than FP16 for a small\n"
          "  quality loss (part 3). Speed on CPU is roughly memory-bandwidth bound:\n"
          "  every output token reads ALL weights once, so smaller = faster too.")


# ============================================================================
# PART 3: Quantization by hand
# ============================================================================
#   QUANTIZE ONE BLOCK OF WEIGHTS TO 4 BITS
#   floats  [ 0.12, -0.53, 0.88, -0.07, ... ]        32 bits each
#      │  scale = max(|w|) / 7      (4-bit signed ints: -8..7)
#      ▼
#   ints    [  1,   -4,    7,    -1,   ... ]         4 bits each + 1 scale
#      │  dequantize at run time: w ~= int x scale
#      ▼
#   floats' [ 0.13, -0.50, 0.88, -0.13, ... ]  error = small, size /8

def quantize_block(ws: list[float], bits: int) -> tuple[list[int], float]:
    qmax = 2 ** (bits - 1) - 1
    scale = max(abs(w) for w in ws) / qmax or 1.0
    return [max(-qmax - 1, min(qmax, round(w / scale))) for w in ws], scale


def part3_quantization():
    header("PART 3 -- Quantization: fewer bits per weight, measured")
    rng = random.Random(15)
    weights = [rng.gauss(0, 0.4) for _ in range(4096)]
    block = 32                                         # GGUF quantizes in small blocks
    print(f"  4096 random weights, blocks of {block}, one scale per block\n")
    print(f"  {'format':<8}{'bits/weight':>12}{'size':>10}{'mean |error|':>14}{'max |error|':>13}")
    for bits in (16, 8, 4, 3, 2):
        errs = []
        for i in range(0, len(weights), block):
            chunk = weights[i:i + block]
            if bits == 16:
                errs += [0.0] * len(chunk)
                continue
            q, s = quantize_block(chunk, bits)
            errs += [abs(w - qi * s) for w, qi in zip(chunk, q)]
        eff_bits = bits if bits == 16 else bits + 16 / block   # + the per-block scale
        size = len(weights) * eff_bits / 8
        print(f"  {('FP16' if bits == 16 else f'Q{bits}'):<8}{eff_bits:>12.2f}{size:>9.0f}B"
              f"{sum(errs) / len(errs):>14.4f}{max(errs):>13.4f}")
    demo = [0.12, -0.53, 0.88, -0.07, 0.31, -0.29]      # the block from the diagram
    q, s = quantize_block(demo, 4)
    print("\n  weights (FP16)    :", demo)
    print("  stored as 4-bit   :", q, f" + one scale {s:.4f}")
    print("  dequantized       :", [round(qi * s, 2) for qi in q])
    print("\n  Error grows fast below 4 bits -- that is why Q4 is the sweet spot.")


# ============================================================================
# PART 4: PATH A -- Ollama (install, pull, run, call over HTTP)
# ============================================================================
#   ONE CALL TO A LOCAL MODEL
#   your Python ──POST /api/chat──▶ Ollama server :11434 ──▶ model on CPU/GPU
#        ▲        {model, messages,        │ loads weights on first call
#        │         stream:false}           │ (load_duration), then generates
#        └──────── {message, eval_count, eval_duration, done_reason} ◀──┘
#   Same shape as the cloud APIs in lesson 03 -- only the URL changes.
#   OpenAI-compatible too:  http://127.0.0.1:11434/v1/chat/completions

INSTALL_STEPS = """\
  1. Install Ollama (Windows / macOS / Linux): download from https://ollama.com/download
     Windows alternative:  winget install Ollama.Ollama
  2. Pull a small model (pick from https://ollama.com/library):
        ollama pull qwen2.5:0.5b      (~0.4 GB, fastest)
        ollama pull llama3.2:1b       (~1.3 GB)
  3. Try it in the terminal:   ollama run qwen2.5:0.5b "Explain a token in one line"
  4. Re-run this lesson: part 4 will call it over HTTP and time it."""


def ollama(path: str, body: dict | None = None, timeout: float = 120.0) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(OLLAMA + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def ollama_stream(model: str, prompt: str):
    """Streaming = newline-delimited JSON chunks, one per few tokens (lesson 06 TTFT)."""
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": True}
    req = urllib.request.Request(OLLAMA + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        for line in r:
            chunk = json.loads(line)
            yield chunk


def part4_ollama(model: str, prompt: str):
    header("PART 4 -- PATH A: Ollama")
    try:
        tags = ollama("/api/tags", timeout=2)
    except (urllib.error.URLError, OSError):
        print("  Ollama is not running on this machine (nothing at 127.0.0.1:11434).\n")
        print(INSTALL_STEPS)
        return
    local = [m["name"] for m in tags.get("models", [])]
    print("  Ollama is running. Local models:", local or "none yet")
    if not local:
        print(f"\n  Pull one first:  ollama pull {model}")
        return
    if model not in local:
        print(f"  '{model}' not pulled -> using '{local[0]}' instead (ollama pull {model} to get it)")
        model = local[0]
    for m in tags["models"]:
        if m["name"] == model:
            d = m.get("details", {})
            print(f"  {model}: {d.get('parameter_size', '?')} params, {d.get('quantization_level', '?')}, "
                  f"{d.get('format', '?')}, {gb(m.get('size', 0)).strip()} on disk")

    # 1) one non-streaming call -- read the same fields as lesson 03
    t0 = time.perf_counter()
    r = ollama("/api/chat", {"model": model, "stream": False,
                             "messages": [{"role": "user", "content": prompt}],
                             "options": {"temperature": 0.2, "num_predict": 120}})
    wall = time.perf_counter() - t0
    ns = 1e9
    print(f"\n  prompt : {prompt}")
    print(f"  answer : {r['message']['content'].strip()[:300]}")
    print(f"  done_reason={r.get('done_reason')}  input tokens={r.get('prompt_eval_count')}  "
          f"output tokens={r.get('eval_count')}")
    if r.get("eval_duration"):
        print(f"  load {r.get('load_duration', 0) / ns:.2f}s | prompt {r.get('prompt_eval_duration', 0) / ns:.2f}s"
              f" | generate {r['eval_duration'] / ns:.2f}s = {r['eval_count'] / (r['eval_duration'] / ns):.1f}"
              f" tokens/sec | wall {wall:.2f}s")

    # 2) streaming -- first text arrives long before the end
    t0 = time.perf_counter()
    first, pieces = None, []
    for chunk in ollama_stream(model, "Count from 1 to 5, comma separated."):
        if first is None and chunk.get("message", {}).get("content"):
            first = time.perf_counter() - t0
        pieces.append(chunk.get("message", {}).get("content", ""))
    total = time.perf_counter() - t0
    print(f"\n  streamed: {''.join(pieces).strip()!r}")
    print(f"  first text after {first or 0:.2f}s, finished after {total:.2f}s  (lesson 06: TTFT)")

    # 3) structured output -- Ollama accepts a JSON schema in `format` (lesson 13)
    schema = {"type": "object", "properties": {"sentiment": {"type": "string",
              "enum": ["positive", "negative", "neutral"]}}, "required": ["sentiment"]}
    r = ollama("/api/chat", {"model": model, "stream": False, "format": schema,
                             "messages": [{"role": "user", "content": "Sentiment of: 'I love this phone'"}]})
    print(f"  structured: {r['message']['content'].strip()}  <- constrained to the schema")


# ============================================================================
# PART 5: PATH B -- "clone" a model from Hugging Face
# ============================================================================
#   WHAT IS INSIDE A MODEL REPO                     huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
#   ├── config.json            architecture: layers, heads, hidden size (lesson 12)
#   ├── model.safetensors      THE WEIGHTS (~1 GB for 0.5B in BF16)
#   ├── tokenizer.json         vocab + merge rules (lesson 01)
#   ├── tokenizer_config.json  chat template (lesson 03)
#   └── generation_config.json default temperature / top_p (lesson 02)
#   git clone (needs git-lfs for the big files)   or   hf download (resumable, faster)

CLONE_STEPS = f"""\
  Option 1 -- git (big files need Git LFS: https://git-lfs.com):
        git lfs install
        git clone https://huggingface.co/{HF_REPO} "{HF_DIR}"
  Option 2 -- Hugging Face CLI (resumable):
        powershell -ExecutionPolicy ByPass -c "irm https://hf.co/cli/install.ps1 | iex"
        hf download {HF_REPO} --local-dir "{HF_DIR}"
  Then run it (installs transformers + torch into a throwaway env, ~1 GB):
        uv run advanced/15b_run_with_transformers.py
  Gated models (e.g. meta-llama/*): accept the licence on the model page,
  then `hf auth login` before downloading."""


def part5_huggingface():
    header("PART 5 -- PATH B: clone a model from Hugging Face")
    if not HF_DIR.exists():
        print(f"  No local copy at {HF_DIR}\n")
        print(CLONE_STEPS)
        return
    print(f"  Found {HF_DIR}:")
    total = 0
    for f in sorted(HF_DIR.iterdir()):
        if f.is_file():
            total += f.stat().st_size
            print(f"    {f.name:<28}{f.stat().st_size / 1024**2:>10.1f} MB")
    cfg = HF_DIR / "config.json"
    if cfg.exists():
        c = json.loads(cfg.read_text(encoding="utf-8"))
        print(f"\n  config: {c.get('num_hidden_layers')} layers, {c.get('num_attention_heads')} heads, "
              f"hidden {c.get('hidden_size')}, vocab {c.get('vocab_size')}, "
              f"context {c.get('max_position_embeddings')}  (the numbers lesson 12 explains)")
    print(f"  total {total / 1024**3:.2f} GB.  Run it:  uv run advanced/15b_run_with_transformers.py")


# ============================================================================
# PART 6: Choosing a model, licences, and reusing the earlier lessons
# ============================================================================
#   PICK A MODEL
#   your RAM (part 2) ──▶ max size ──▶ task? ─┬─ chat / general ──▶ Llama, Qwen, Gemma
#                                              ├─ code           ──▶ Qwen-Coder, DeepSeek-Coder
#                                              ├─ embeddings/RAG ──▶ nomic-embed, bge (lesson 10)
#                                              └─ reasoning       ──▶ distilled "R1"/thinking variants
#   then: licence OK for your use? ──▶ run YOUR eval set (lesson 11) ──▶ decide

def part6_choose():
    header("PART 6 -- Choosing a model, licences, reusing earlier lessons")
    checks = [
        "Licence: Apache-2.0 / MIT = broadly free; Llama & Gemma have their own terms -- read them",
        "Size: largest model that fits at Q4 in ~60% of RAM (part 2)",
        "Context length: check config.json / the model card -- local KV cache grows with it",
        "Quality: run lesson 11's eval loop on YOUR task, local vs API, before switching",
        "Security: weights are code-adjacent -- prefer safetensors/GGUF from known publishers",
    ]
    for c in checks:
        print("  [ ]", c)
    print("\n  Reuse everything you learned: Ollama speaks the OpenAI chat format, so\n"
          "  most SDK code only needs a different base URL:")
    print('      OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")')
    print("  Tool calling (lesson 07), JSON schemas (lesson 13) and RAG (lesson 10)\n"
          "  all work the same way -- smaller models are just less reliable at them.")


def main():
    ap = argparse.ArgumentParser(description="Run an open-source model locally")
    ap.add_argument("--model", default="qwen2.5:0.5b", help="Ollama model tag")
    ap.add_argument("--prompt", default="In one sentence, what is a token?")
    args = ap.parse_args()
    part1_why_local()
    part2_will_it_fit()
    part3_quantization()
    part4_ollama(args.model, args.prompt)
    part5_huggingface()
    part6_choose()


if __name__ == "__main__":
    main()

# Key takeaway: an open model is just files. Check it fits (params x bits / 8),
# prefer Q4, start with Ollama, and judge it with YOUR eval set, not vibes.
# Exercise: pull two sizes (0.5b and 3b), run the same 10 prompts through both
# via part 4's ollama() helper, and compare tokens/sec and answer quality.
