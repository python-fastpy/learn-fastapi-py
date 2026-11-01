r"""01 -- REQUEST: what happens the moment you press Enter
=========================================================

CONCEPT IN ONE LINE:
  Your text leaves your program as a JSON body in an HTTP POST; the Ollama server finds the
  model file on disk, loads its 2 GB of weights into memory, and only THEN can the model run.

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ [01 request] ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax

WHAT HAPPENS:

   ┌──────────────────────────┐
   │ YOU TYPE                 │  "Say hi in one word."
   │ (chat app, script, curl) │
   └────────────┬─────────────┘
                ▼  your code puts it in a JSON body
   ┌──────────────────────────────────────────────────────────────┐
   │ HTTP POST http://localhost:11434/api/chat                    │
   │ {                                                            │
   │   "model": "llama3.2",                <- WHICH model         │
   │   "messages": [                       <- the conversation    │
   │     {"role": "user", "content": "Say hi in one word."}       │
   │   ],                                                         │
   │   "stream": false,                    <- one JSON at the end │
   │   "options": {"temperature": 0},      <- sampling settings   │
   │   "keep_alive": "5m"                  <- keep it loaded      │
   │ }                                                            │
   └────────────┬─────────────────────────────────────────────────┘
                ▼  arrives at the Ollama SERVER (a program on your machine, port 11434)
   ┌──────────────────────────────────────────────────────────────┐
   │ 1. RESOLVE the name  "llama3.2"  ->  "llama3.2:latest"       │
   │    ~/.ollama/models/manifests/registry.ollama.ai/            │
   │        library/llama3.2/latest      (small JSON "manifest")  │
   │    -> layer "application/vnd.ollama.image.model"             │
   │    -> ~/.ollama/models/blobs/sha256-dde5aa3f...  (2.0 GB)    │
   │                                                              │
   │ 2. LOAD (only if not already in memory)                      │
   │    read the GGUF file -> weights into RAM / GPU VRAM         │
   │    time spent = "load_duration" in the response              │
   │                                                              │
   │ 3. KEEP it loaded for keep_alive (default 5 minutes)         │
   │    so the next request skips step 2                          │
   └────────────┬─────────────────────────────────────────────────┘
                ▼
          02 template (next file) ...

  THE MANIFEST -- why "llama3.2" finds the right file:
     The model name is just a label. The manifest is a tiny JSON listing the pieces of the
     download, each by its sha256 hash (the hash IS the file name in blobs/):

        mediaType ...image.model      -> the GGUF: weights + vocabulary + metadata (2.0 GB)
        mediaType ...image.template   -> the chat template (02_template.py)
        mediaType ...image.license    -> license text
        mediaType ...image.params     -> default parameters (the stop words, 11_stop.py)

  COLD vs WARM -- the same request, twice (real numbers from main() below):

        call 1 (model NOT loaded)   load_duration ≈ 1.9 s    <- reading 2 GB from disk
        call 2 (model loaded)       load_duration ≈ 0.01 s   <- already in memory
     (cold loads measured 1.9 - 3.6 s on this machine; it depends on disk speed and on what
      else is running)

     On a CPU-only machine (size_vram 0 below) the weights live in normal RAM. With a GPU
     they go to VRAM and everything after this step is much faster.

  WHAT /api/ps SHOWS while the model is loaded:
        "size": 2567826307          <- 2.57 GB in memory: 2.0 GB weights + KV cache + buffers
        "size_vram": 0              <- 0 = running on CPU only (no GPU used)
        "context_length": 4096      <- how many tokens it was loaded for (Ollama's default
                                       num_ctx; the model itself supports 131,072)
        "expires_at": "...12:29"    <- loaded time + keep_alive; then it's unloaded

  ANATOMY OF THE REQUEST BODY (/api/chat):
        field         required?   meaning
        model         yes         name:tag of a model you pulled ("llama3.2" = "llama3.2:latest")
        messages      yes         list of {"role": "system"|"user"|"assistant"|"tool",
                                  "content": "..."} -- the WHOLE conversation, every time
        stream        no          true (default) = many small JSON chunks; false = one at the end
        options       no          temperature, top_k, top_p, seed, num_predict, num_ctx, stop ...
        keep_alive    no          "5m" (default), "1h", 0 = unload right after, -1 = forever
        format        no          "json" or a JSON schema -> structured output (lesson 09)
        tools         no          functions the model may call (lesson 10)

WHERE THIS COMES FROM:
   - the text and the JSON body          -> YOUR code
   - the endpoint, defaults, keep_alive  -> the Ollama SERVER (localhost:11434)
   - the manifest + blobs                -> created by `ollama pull llama3.2`
   - the GGUF file                       -> Meta's weights, converted + quantized (Q4_K_M)
                                            and published on registry.ollama.ai

IS IT OLLAMA-SPECIFIC?
   piece                 the model itself   Ollama              OpenAI                  Anthropic                 Hugging Face transformers
   where it runs         -                  your machine        their servers           their servers             your machine (Python)
   endpoint              -                  POST /api/chat      POST /v1/chat/          POST /v1/messages         no server: model.generate()
                                                                completions
   auth                  -                  none (local)        Authorization:          x-api-key: ... +          none (local)
                                                                Bearer <key>            anthropic-version header
   loading weights       -                  you see it          hidden                  hidden                    from_pretrained() -- you
                                            (load_duration)                                                       wait for it yourself
   max output tokens     -                  optional            optional                REQUIRED (max_tokens)     max_new_tokens
                                            (num_predict)       (max_tokens / ...)
   The MODEL never sees HTTP or JSON -- it only ever receives token IDs (03_tokens.py).
   Everything in this file is the "delivery service" around it.

   The same request in other APIs (shapes only, hedged -- check each provider's docs):
     OpenAI     POST https://api.openai.com/v1/chat/completions
                headers: Authorization: Bearer $OPENAI_API_KEY
                body:    {"model": "...", "messages": [{"role": "user", "content": "..."}]}
     Anthropic  POST https://api.anthropic.com/v1/messages
                headers: x-api-key: $ANTHROPIC_API_KEY, anthropic-version: 2023-06-01
                body:    {"model": "...", "max_tokens": 100,
                          "messages": [{"role": "user", "content": "..."}]}
                (system prompt goes in a top-level "system" field, not in messages)

COMMON CONFUSIONS:
   - "The model remembers our chat."  No -- the app resends ALL messages in every request.
   - "Ollama is the model."  No -- Ollama is the server; llama3.2 is the model file it runs.
   - "The first answer is slow because the model is thinking."  Mostly it's load_duration:
     reading 2 GB from disk. The second call is fast.
   - "size 2.0 GB on disk = 2.0 GB in memory."  Memory is bigger (2.57 GB here) because the
     KV cache for the context (10_loop.py) and work buffers are added.
   - "wall clock" > total_duration.  total_duration is measured INSIDE Ollama. Your program
     also waits for the network and for other requests in the queue. On this Windows machine
     "localhost" added ~2 s to EVERY call: it tries IPv6 (::1) first, fails, then falls back
     to IPv4. Measured with /api/version:
          http://localhost:11434    2.5 s
          http://127.0.0.1:11434    0.4 s
     If your calls feel slow on Windows, use http://127.0.0.1:11434.
"""

import json
import time

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def show_loaded(label):
    loaded = httpx.get(OLLAMA + "/api/ps", timeout=30).json()["models"]
    print(f"{label}: {len(loaded)} model(s) in memory")
    for m in loaded:
        print(f"   {m['name']}  size={m['size']:,} bytes  size_vram={m['size_vram']:,}"
              f"  context_length={m.get('context_length')}  expires_at={m['expires_at']}")


def chat(text):
    body = {
        "model": CHAT_MODEL,
        "messages": [{"role": "user", "content": text}],
        "stream": False,
        "options": {"temperature": 0},
        "keep_alive": "5m",
    }
    t0 = time.perf_counter()
    resp = httpx.post(OLLAMA + "/api/chat", json=body, timeout=300)
    resp.raise_for_status()
    r = resp.json()
    wall = time.perf_counter() - t0
    print(f"   answer={r['message']['content']!r}  load_duration={r['load_duration'] / 1e9:.2f} s"
          f"  total_duration={r['total_duration'] / 1e9:.2f} s  (wall clock {wall:.2f} s)")


def main():
    print("STEP 1: which models are on disk? (/api/tags)")
    tags = httpx.get(OLLAMA + "/api/tags", timeout=30).json()
    for m in tags["models"]:
        print(f"   {m['name']}  {m['size']:,} bytes  {m['details']['parameter_size']}"
              f"  {m['details']['quantization_level']}  digest={m['digest'][:12]}...")
    # -> llama3.2:latest  2,019,393,189 bytes  3.2B  Q4_K_M  digest=a80c4f17acd5...
    #    (the digest here is of the MANIFEST; the GGUF blob has its own sha256-dde5aa3f...)

    print("\nSTEP 2: unload it, so we can watch a cold start (keep_alive: 0)")
    httpx.post(OLLAMA + "/api/generate", json={"model": CHAT_MODEL, "keep_alive": 0}, timeout=60)
    time.sleep(1)
    show_loaded("before")
    # -> before: 0 model(s) in memory

    print("\nSTEP 3: the same request twice")
    print("call 1 (cold):")
    chat("Say hi in one word.")
    print("call 2 (warm):")
    chat("Say hi in one word.")
    # -> call 1 (cold):
    #       answer='Hello.'  load_duration=1.89 s  total_duration=2.21 s  (wall clock 4.67 s)
    #    call 2 (warm):
    #       answer='Hello.'  load_duration=0.01 s  total_duration=0.13 s  (wall clock 2.65 s)
    #    (wall clock is ~2.5 s more each time: the "localhost" delay, see COMMON CONFUSIONS)

    print()
    show_loaded("after")
    # -> after: 1 model(s) in memory
    #       llama3.2:latest  size=2,567,826,307 bytes  size_vram=0  context_length=4096
    #       expires_at=2026-11-01T12:29:38.0164829+05:30

    print("\nSTEP 4: where the model file came from (the manifest)")
    from pathlib import Path
    manifest = (Path.home() / ".ollama" / "models" / "manifests" / "registry.ollama.ai"
                / "library" / CHAT_MODEL / "latest")
    for layer in json.loads(manifest.read_text())["layers"]:
        print(f"   {layer['mediaType']:<45} {layer['size']:>13,}  {layer['digest'][:19]}...")
    # -> application/vnd.ollama.image.model             2,019,377,376  sha256:dde5aa3fc5f...
    #    application/vnd.ollama.image.template                  1,429  sha256:966de95ca8a...
    #    application/vnd.ollama.image.license                   7,711  sha256:fcc5a6bec9d...
    #    application/vnd.ollama.image.license                   6,016  sha256:a70ff7e570d...
    #    application/vnd.ollama.image.params                       96  sha256:56bb8bd477a...
    #    application/vnd.docker.distribution.manifest.v2+json  1,005  sha256:a80c4f17acd...
    #    (the last one is the manifest itself -- its hash is the digest /api/tags shows;
    #     the .model blob is ~/.ollama/models/blobs/sha256-dde5aa3f... -- the file
    #     gguf_reader.py opens in the later lessons)


if __name__ == "__main__":
    main()

# Try: send "keep_alive": 0 in chat() -- every call becomes a cold start (watch load_duration).
