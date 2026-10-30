"""15 -- Run open models locally  (simple version, includes 15b)
===============================================================

IN ONE LINE:
  An open model is just a big file of numbers. You download it once and
  run it on your own computer: no API key, no bill, no data leaves.

REAL USE CASE:
  Your company does not allow customer data to go to a cloud API.
  So your FastAPI app calls a model that runs on the same machine:

     your FastAPI app
          │  POST http://127.0.0.1:11434/api/chat   (same shape as a cloud API)
          ▼
     ┌──────────────────┐      loads      ┌──────────────────────────┐
     │  Ollama server   │ ◀────────────── │ model file (e.g. 0.4 GB) │
     └──────────────────┘                 └──────────────────────────┘
          │  runs on YOUR CPU / GPU
          ▼
     answer

WHAT RUNS WHERE (everything is inside YOUR PC, nothing goes to the internet):

  ┌──────────────────────────────────────── YOUR PC ─────────────────────────────────────────┐
  │                                                                                          │
  │  ┌──────────────┐ POST /chat ┌──────────────────┐  PATH A: HTTP   ┌──────────────────┐   │
  │  │   Browser    │ ─────────▶ │  YOUR FASTAPI    │ ──────────────▶ │  Ollama server   │   │
  │  └──────────────┘            │  (port 8000)     │  127.0.0.1:     │  (port 11434)    │   │
  │                              │                  │  11434/api/chat │                  │   │
  │                              │                  │                 └──────────────────┘   │
  │                              │                  │  PATH B: import                        │
  │                              │                  │ ──────────────▶ ┌──────────────────┐   │
  │                              └──────────────────┘  transformers   │ transformers     │   │
  │                                                    (same process) │ (Python library) │   │
  │                                                                   └──────────────────┘   │
  │                                                                            │             │
  │                                                                            ▼ load once   │
  │   ┌───────────────────────────────────────────────────────────────────────────────────┐  │
  │   │ MODEL FILE on disk: billions of numbers (weights). Copied into RAM / GPU memory.  │  │
  │   │ size = parameters x bits / 8   ◀── STEP 1.  Fewer bits per weight ◀── STEP 2.     │  │
  │   └───────────────────────────────────────────────────────────────────────────────────┘  │
  │   Path A or path B: both read the same kind of file. It runs on YOUR CPU / GPU.          │
  └──────────────────────────────────────────────────────────────────────────────────────────┘

WILL IT FIT? one worked example (8B model, 16 GB laptop), numbers from STEP 1:

   8,000,000,000 parameters
        │
        ▼  x bits per weight
   16-bit:  8,000,000,000 x 16 = 128,000,000,000 bits ──▶ ÷ 8 = 16,000,000,000 bytes = 16.0 GB  ✗
    8-bit:  8,000,000,000 x  8 =  64,000,000,000 bits ──▶ ÷ 8 =  8,000,000,000 bytes =  8.0 GB  ~
    4-bit:  8,000,000,000 x  4 =  32,000,000,000 bits ──▶ ÷ 8 =  4,000,000,000 bytes =  4.0 GB  ✓
        │
        ▼  compare with your RAM (16 GB), keep room for the OS + KV cache
   16.0 GB: no room at all ✗     8.0 GB: tight ~     4.0 GB: fits well ✓
   70B at 4-bit = 35.0 GB ──▶ does NOT fit a 16 GB laptop, at any of these sizes.

WHAT AN ENGINEER MUST KNOW:
  1. First question: does it FIT? memory = parameters x bits per weight / 8.
  2. Quantization stores each weight in fewer bits (8 or 4). Q4 is the
     usual choice: about 4x smaller, only a small loss in quality.
  3. Start with Ollama (easiest). Use Python "transformers" for research
     and fine-tuning (that was lesson 15b, now merged here).
  4. Local models are smaller and less smart than the best API models.
     Test them on YOUR task before you switch.

Run:  uv run python simple/15_run_open_models_locally.py
"""

# ============================================================================
# HOW TO DO IT FOR REAL (not run here: needs Ollama or extra packages)
# ============================================================================
# PATH A -- Ollama (easiest):
#   winget install Ollama.Ollama
#   ollama pull qwen2.5:0.5b
#   ollama run qwen2.5:0.5b "Explain a token in one line"
#   Then from Python (standard library):
#     import json, urllib.request
#     body = {"model": "qwen2.5:0.5b", "stream": False,
#             "messages": [{"role": "user", "content": "Hi"}]}
#     req = urllib.request.Request("http://127.0.0.1:11434/api/chat",
#                                  data=json.dumps(body).encode(),
#                                  headers={"Content-Type": "application/json"})
#     print(json.loads(urllib.request.urlopen(req).read())["message"]["content"])
#   It also speaks the OpenAI format: base_url="http://127.0.0.1:11434/v1"
#
# PATH B -- Hugging Face + transformers (needs: transformers, torch, ~1 GB):
#   hf download Qwen/Qwen2.5-0.5B-Instruct --local-dir models/qwen
#     from transformers import AutoModelForCausalLM, AutoTokenizer
#     tok = AutoTokenizer.from_pretrained("models/qwen")
#     model = AutoModelForCausalLM.from_pretrained("models/qwen")
#     msgs = [{"role": "user", "content": "Hi"}]
#     text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
#     out = model.generate(**tok(text, return_tensors="pt"), max_new_tokens=50)
#     print(tok.decode(out[0], skip_special_tokens=True))
# ============================================================================


# ----------------------------------------------------------------------------
# STEP 1: WILL IT FIT? memory = parameters x bits / 8
# ----------------------------------------------------------------------------
#   parameters (0.5e9, 8e9, 70e9)   bits (16, 8, 4)
#            │                         │
#            └────────────┬────────────┘
#                         ▼
#          parameters x bits       = total bits
#                         │
#                         ▼  ÷ 8   (8 bits = 1 byte)
#                     total bytes
#                         │
#                         ▼  ÷ 1,000,000,000
#                     GB  ──▶  table:   model   16-bit   8-bit   4-bit
#                                       0.5B       1.0     0.5     0.2
#                                       8B        16.0     8.0     4.0
#                                       70B      140.0    70.0    35.0
def model_memory_gb(parameters, bits):
    return parameters * bits / 8 / 1_000_000_000


# ----------------------------------------------------------------------------
# STEP 2: QUANTIZE = store each weight as a small whole number + one scale
# ----------------------------------------------------------------------------
#   original weights:  [0.12, -0.53, 0.88, -0.07, 0.31, -0.29]
#      │
#      ▼  scale = biggest |weight| / 7 = 0.88 / 7 = 0.13   (one number, shared)
#      │
#      ▼  quantize: round(weight / scale)  ──▶ whole numbers from -8 to 7
#
#      weight   ÷ scale   round   stored   x scale   used at run   error
#      ───────  ───────   ─────   ──────   ───────   ───────────   ─────
#       0.12      0.95    ──▶       1      ──▶          0.13        0.01
#      -0.53     -4.22    ──▶      -4      ──▶         -0.50        0.03
#       0.88      7.00    ──▶       7      ──▶          0.88        0.00
#      -0.07     -0.56    ──▶      -1      ──▶         -0.13        0.06
#       0.31      2.47    ──▶       2      ──▶          0.25        0.06
#      -0.29     -2.31    ──▶      -2      ──▶         -0.25        0.04
#                                                                 ─────
#                                                     average error 0.03
#   16 bits per weight ──▶ 4 bits per weight = 4x smaller file, tiny error.
def quantize_4bit(weights):
    """4-bit numbers go from -8 to 7. One shared 'scale' turns them back."""
    scale = max(abs(w) for w in weights) / 7
    small_ints = [round(w / scale) for w in weights]
    return small_ints, scale


def dequantize(small_ints, scale):
    """What the model uses at run time: a close copy of the original."""
    return [round(i * scale, 2) for i in small_ints]


def main():
    print("STEP 1: will it fit? (weights only, in GB)")
    print(f"  {'model':<6} {'16-bit':>8} {'8-bit':>8} {'4-bit':>8}")
    for name, params in [("0.5B", 0.5e9), ("8B", 8e9), ("70B", 70e9)]:
        sizes = [model_memory_gb(params, bits) for bits in (16, 8, 4)]
        print(f"  {name:<6} {sizes[0]:>8.1f} {sizes[1]:>8.1f} {sizes[2]:>8.1f}")
    print("  A laptop with 16 GB RAM: 8B at 4-bit fits (4 GB). 70B does not.")
    print("  Keep extra room for the OS and the KV cache (longer prompt = more memory).")

    print("\nSTEP 2: quantize 6 weights to 4 bits")
    weights = [0.12, -0.53, 0.88, -0.07, 0.31, -0.29]
    small_ints, scale = quantize_4bit(weights)
    back = dequantize(small_ints, scale)
    errors = [abs(a - b) for a, b in zip(weights, back)]
    print(f"  original     : {weights}")
    print(f"  stored (4bit): {small_ints}  + scale {scale:.2f}")
    print(f"  used at run  : {back}")
    print("  one by one   : weight  ÷ scale  stored  used   error")
    for w, i, b in zip(weights, small_ints, back):
        print(f"                 {w:>6.2f}  {w / scale:>7.2f}  {i:>6}  {b:>5.2f}  {abs(w - b):.2f}")
    print(f"  average error: {sum(errors) / len(errors):.2f}  (small, and the file is 4x smaller)")

    print("\nSTEP 3: which tool?")
    print("  Ollama       -> start here, one installer, HTTP API on port 11434")
    print("  LM Studio    -> desktop app with a chat window, no code")
    print("  transformers -> Python, full control, research and fine-tuning")
    print("  vLLM         -> GPU server for many users at the same time")
    print("  (See 'HOW TO DO IT FOR REAL' at the top of this file.)")


if __name__ == "__main__":
    main()

# Remember:
#   - Open model = files you download. Check memory first: params x bits / 8.
#   - 4-bit (Q4) is the normal choice for local use.
#   - Ollama is the easy way; it looks like any chat API to your code.
# Try: add ("3B", 3e9) to the list in STEP 1. Does it fit on your machine?
