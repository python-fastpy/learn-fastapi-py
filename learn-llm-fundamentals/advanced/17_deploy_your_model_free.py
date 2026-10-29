"""Lesson 17 -- Deploy "our own model" and use it for FREE
==========================================================

WHY THIS MATTERS:
  Lesson 16 built "our own model with our context": a local open model
  (Ollama) + our handbook in the prompt. It only works on YOUR laptop, from
  a Python script. Deploying = turning it into a URL that other programs
  and people can call -- and you can do every step without paying.

     your laptop (lesson 16)              deployed (this lesson)
     ┌───────────────────────┐            ┌──────────────────────────────────┐
     │ python script         │            │ POST https://<your-url>/ask      │
     │  └ retrieve + prompt  │   ──▶      │  {"question": "..."}             │
     │  └ Ollama :11434      │            │  ◀── {"answer": ..., "sources"}  │
     └───────────────────────┘            └──────────────────────────────────┘

  THE FREE PATH, STEP BY STEP
     step 1  wrap it in an HTTP API           (part 2 -- runs for real here)
     step 2  share it from your laptop        Cloudflare Tunnel / ngrok   (part 3)
     step 3  host it 24/7                     Oracle Always Free VM, HF Spaces (part 4)
     step 4  publish your model weights       Hugging Face Hub, Ollama registry (part 5)
     or      skip hosting: free API tiers     Groq, Gemini, OpenRouter ... (part 6)

WHAT YOU'LL LEARN:
  1. What "deploy" means for an LLM app, and the free options for each piece
  2. Step 1 for real: an /ask API around lesson 16's RAG + Ollama (stdlib only)
  3. Step 2: give your laptop a public HTTPS URL for free
  4. Step 3: run it 24/7 on free hosting -- what fits in the free hardware
  5. Step 4: publish a fine-tuned model (lesson 14) so anyone can run it
  6. No hosting at all: free hosted-model API tiers, and their catches
  7. The safety checklist before anything goes public

Concepts:
  - Endpoint: a URL + method your code answers (POST /ask)
  - Tunnel: a free relay that gives a local port a public HTTPS URL
  - Always-free tier: a cloud VM / Space that costs nothing, within limits
  - Cold start: the first request after idle waits for the model to load
  - API key: a shared secret the caller sends, so strangers can't use your model

NOTE: free tiers, limits and prices change often. The numbers below were
correct when this lesson was written -- check each provider's page first.

PREREQUISITES: Lessons 15 and 16. Pure Python standard library.
Part 2 answers questions only if Ollama is running (lesson 15).

Level: ADVANCED
Run:  uv run python advanced/17_deploy_your_model_free.py                  (guide + self-test)
      uv run python advanced/17_deploy_your_model_free.py --serve          (step 1: run the API)
      uv run python advanced/17_deploy_your_model_free.py --serve --key mysecret --host 0.0.0.0
"""

import argparse
import hmac
import importlib.util
import json
import os
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Reuse lesson 16 (retrieve, build_prompt, ask_ollama, ollama_up) -- the file
# name starts with a digit, so it is loaded by path instead of `import`.
_spec = importlib.util.spec_from_file_location(
    "lesson16", Path(__file__).with_name("16_own_model_with_your_context.py"))
assert _spec is not None and _spec.loader is not None
lesson16 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lesson16)

DEFAULT_MODEL = "qwen2.5:0.5b"


def header(title: str):
    print(f"\n######## {title} ########\n")


# ============================================================================
# PART 1: What "deploy" means -- and the free option for each piece
# ============================================================================
#   THREE PIECES, EACH CAN BE FREE
#   ┌────────────────┐     ┌────────────────────┐     ┌───────────────────────┐
#   │ YOUR API       │ ──▶ │ THE MODEL          │     │ A PUBLIC URL          │
#   │ /ask: retrieve │     │ Ollama + weights   │     │ so others can call it │
#   │ + prompt       │     │ (or a hosted API)  │     │                       │
#   └────────────────┘     └────────────────────┘     └───────────────────────┘
#     this lesson          your laptop / free VM      tunnel / free host

def part1_map():
    header("PART 1 -- What 'deploy' means, and the free options")
    rows = [
        ("laptop + tunnel", "your PC", "only while PC is on", "demos, testing with friends"),
        ("Oracle Always Free VM", "4 ARM cores, 24 GB RAM", "24/7", "a real small service (7-8B Q4 fits)"),
        ("Hugging Face Space", "2 vCPU, 16 GB RAM", "sleeps when idle", "public demos (0.5-3B models)"),
        ("Colab / Kaggle", "free GPU, hours", "session only", "fine-tuning & tests -- NOT serving"),
        ("free API tier", "provider's GPUs", "24/7, rate-limited", "no hosting at all (part 6)"),
    ]
    print(f"  {'option':<24}{'free hardware':<25}{'uptime':<21}best for")
    for r in rows:
        print(f"  {r[0]:<24}{r[1]:<25}{r[2]:<21}{r[3]}")
    print("\n  Same app everywhere: only WHERE Ollama runs and HOW the URL is made change.")


# ============================================================================
# PART 2: Step 1 -- wrap lesson 16 in an HTTP API
# ============================================================================
#   ONE REQUEST THROUGH OUR API
#   client ──POST /ask {"question"} + X-API-Key──▶ our server (:8017)
#            │ 1. check the key          (401 if wrong)
#            │ 2. retrieve handbook lines (lesson 16 part 4)
#            │ 3. build the grounded prompt
#            │ 4. ask Ollama on localhost:11434
#   client ◀──{"answer", "sources", "model"}──┘
#   GET /health ──▶ {"ok": true, "ollama": true/false}   (for uptime checks)
#   Ollama itself stays on 127.0.0.1 -- only OUR API is ever exposed.

def make_handler(model: str, api_key: str | None, quiet: bool = False):
    class AskHandler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: dict):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _authorized(self) -> bool:
            if api_key is None:
                return True
            sent = self.headers.get("X-API-Key", "")
            return hmac.compare_digest(sent.encode(), api_key.encode())   # constant-time compare

        def do_GET(self):
            if self.path == "/health":
                self._send(200, {"ok": True, "ollama": lesson16.ollama_up(), "model": model})
            else:
                self._send(404, {"error": "try GET /health or POST /ask"})

        def do_POST(self):
            if self.path != "/ask":
                return self._send(404, {"error": "try POST /ask"})
            if not self._authorized():
                return self._send(401, {"error": "missing or wrong X-API-Key"})
            try:
                length = int(self.headers.get("Content-Length", 0))
                if length > 10_000:                                       # questions are short
                    return self._send(413, {"error": "request too large"})
                question = json.loads(self.rfile.read(length))["question"].strip()
            except (ValueError, KeyError, AttributeError):
                return self._send(400, {"error": 'send JSON: {"question": "..."}'})
            if not question or len(question) > 500:
                return self._send(400, {"error": "question must be 1-500 characters"})
            hits = lesson16.retrieve(question)
            answer = lesson16.ask_ollama(model, lesson16.build_prompt(question, hits))
            status = 200 if answer else 503
            self._send(status, {"question": question,
                                "answer": answer or "model unavailable -- is Ollama running?",
                                "sources": [h[0] for h in hits], "model": model})

        def log_message(self, fmt, *args):
            if not quiet:
                print(f"    [server] {self.address_string()} {fmt % args}")

    return AskHandler


def call(url: str, body: dict | None = None, key: str | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-API-Key"] = key
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def part2_self_test(model: str):
    header("PART 2 -- Step 1 for real: our /ask API (self-test on a random port)")
    key = "demo-key"
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(model, key, quiet=True))
    base = f"http://127.0.0.1:{server.server_port}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"  started at {base}  (API key: {key!r})\n")
    tests = [
        ("GET /health", f"{base}/health", None, None),
        ("POST /ask, no key", f"{base}/ask", {"question": "How many vacation days do I get?"}, None),
        ("POST /ask, bad body", f"{base}/ask", {"q": "oops"}, key),
        ("POST /ask, with key", f"{base}/ask", {"question": "How many vacation days do I get?"}, key),
    ]
    for label, url, body, k in tests:
        status, resp = call(url, body, k)
        print(f"  {label:<22}-> {status}  {json.dumps(resp)[:110]}")
    server.shutdown()
    print("\n  401 without the key, 400 for a bad body, sources always returned; the\n"
          "  answer is real only if Ollama is running (else 503 + the sources).")
    print("\n  Run it for real (keep this terminal open):")
    print("    uv run python advanced/17_deploy_your_model_free.py --serve --key mysecret")
    print("  Call it (PowerShell):")
    print("    Invoke-RestMethod -Method Post http://127.0.0.1:8017/ask -ContentType 'application/json' `")
    print("      -Headers @{'X-API-Key'='mysecret'} -Body '{\"question\": \"How many vacation days do I get?\"}'")


# ============================================================================
# PART 3: Step 2 -- a public URL for your laptop, free
# ============================================================================
#   TUNNEL = A FREE RELAY
#   friend's browser ──https──▶ abc-xyz.trycloudflare.com ──▶ cloudflared on your PC
#                                                              └─▶ 127.0.0.1:8017 (our API)
#   No router setup, no open ports, HTTPS included. Stops when your PC sleeps.

TUNNEL_STEPS = """\
  Cloudflare quick tunnel (free, no account needed for a temporary URL)
    1. winget install Cloudflare.cloudflared
    2. terminal A:  uv run python advanced/17_deploy_your_model_free.py --serve --key <long-random-key>
    3. terminal B:  cloudflared tunnel --url http://localhost:8017
    4. it prints  https://<random-words>.trycloudflare.com  -> share it + the key
  ngrok (free account, one tunnel)
    1. winget install ngrok.ngrok   then   ngrok config add-authtoken <token>
    2. ngrok http 8017
  ALWAYS use --key: the URL is public, and anyone who finds it gets your model."""


def part3_tunnel():
    header("PART 3 -- Step 2: share it from your laptop (free tunnel)")
    print(TUNNEL_STEPS)


# ============================================================================
# PART 4: Step 3 -- host it 24/7 for free
# ============================================================================
#   WHAT FITS IN FREE HARDWARE (Q4 weights ~0.6 GB per billion params, lesson 15)
#   HF Space  16 GB RAM, 2 CPU   ──▶ 0.5-3B   ok, slow-ish (~5-15 tokens/s)
#   Oracle    24 GB RAM, 4 ARM   ──▶ 7-8B Q4  ok (~5 GB) + room for num_ctx
#   neither has a GPU -- keep models small and answers short (max tokens)

ORACLE_STEPS = """\
  A. Oracle Cloud "Always Free" VM (24/7, the most free power)
    1. sign up at cloud.oracle.com (card needed for identity, not charged on Always Free)
    2. create instance: shape VM.Standard.A1.Flex, 4 OCPU, 24 GB, Ubuntu
    3. ssh in, then:
         curl -fsSL https://ollama.com/install.sh | sh
         ollama pull qwen2.5:3b                 # or llama3.1:8b (Q4, ~5 GB)
         git clone <your repo> && cd learn-llm-fundamentals
         curl -LsSf https://astral.sh/uv/install.sh | sh
         uv run python advanced/17_deploy_your_model_free.py --serve --host 0.0.0.0 --key <key>
    4. open port 8017 in the VCN security list (or skip this and run cloudflared, part 3)
    5. keep it running after logout: a systemd service, or at least  tmux"""

HF_SPACE_STEPS = """\
  B. Hugging Face Space (free CPU, public demo, sleeps after ~48 h idle)
    1. huggingface.co -> New Space -> SDK: Docker -> hardware: CPU basic (free)
    2. add files: this folder + a Dockerfile like:
         FROM ollama/ollama
         RUN apt-get update && apt-get install -y python3
         WORKDIR /app
         COPY . .
         ENV OLLAMA_HOST=127.0.0.1:11434
         ENTRYPOINT []
         CMD ollama serve & sleep 5 && ollama pull qwen2.5:0.5b && \\
             python3 advanced/17_deploy_your_model_free.py --serve --host 0.0.0.0 --port 7860 --key "$API_KEY"
    3. Settings -> Variables and secrets -> add secret API_KEY
    4. git push -> URL: https://<user>-<space>.hf.space/ask
    The model is re-pulled on every cold start: small models only."""


def part4_host():
    header("PART 4 -- Step 3: host it 24/7 for free")
    print(ORACLE_STEPS)
    print()
    print(HF_SPACE_STEPS)
    print("\n  Colab / Kaggle give free GPUs for hours -- use them to FINE-TUNE (lesson 14),\n"
          "  not to serve: the session and its URL die when the notebook stops.")


# ============================================================================
# PART 5: Step 4 -- publish your model weights (fine-tuned in lesson 14)
# ============================================================================
#   WHERE A MODEL FILE CAN LIVE, FREE
#   LoRA adapter / merged weights ──▶ Hugging Face Hub  (public or private repo)
#   GGUF (quantized)              ──▶ Ollama registry   (ollama run you/model)
#   Anyone can then run it on their own machine -- you pay nothing for their use.

PUBLISH_STEPS = """\
  Hugging Face Hub (free repos)
    1. pip install -U huggingface_hub   then   hf auth login   (token from Settings)
    2. hf upload <user>/handbook-qwen-lora ./my_lora_adapter   (add --private to hide it)
    3. others load it with transformers + peft (lesson 15b)
  Ollama registry (free account at ollama.com)
    1. write a Modelfile:   FROM ./handbook-q4_k_m.gguf
                            SYSTEM "You answer questions about the company handbook..."
    2. ollama create <user>/handbook -f Modelfile
    3. ollama push <user>/handbook     ->  anyone:  ollama run <user>/handbook
  NEVER publish a model fine-tuned on private documents: weights can leak
  training text. For private data keep option A (docs in the prompt, lesson 16)."""


def part5_publish():
    header("PART 5 -- Step 4: publish your model weights")
    print(PUBLISH_STEPS)


# ============================================================================
# PART 6: No hosting at all -- free hosted-model API tiers
# ============================================================================
#   SAME PROMPT, SOMEONE ELSE'S GPU
#   our retrieve + build_prompt ──▶ OpenAI-compatible /v1/chat/completions
#                                     ├─ Ollama locally   http://127.0.0.1:11434/v1
#                                     └─ a free API tier  https://<provider>/v1
#   Only the base URL + API key change; the RAG code stays the same.

FREE_APIS = [
    ("Google AI Studio", "Gemini Flash models", "generous daily free quota", "free-tier data may be used to improve models"),
    ("Groq", "Llama, Qwen, gpt-oss", "per-minute/day rate limits", "very fast; open models"),
    ("OpenRouter", "models tagged ':free'", "small daily request cap", "one key, many providers"),
    ("Cloudflare Workers AI", "Llama, Mistral, Qwen", "daily free allowance", "runs at the edge, pairs with part 3"),
    ("Hugging Face Inference", "many open models", "small monthly credit", "same account as part 5"),
]


def part6_free_apis():
    header("PART 6 -- No hosting: free hosted-model API tiers")
    print(f"  {'provider':<24}{'models':<24}{'free limit':<28}note")
    for r in FREE_APIS:
        print(f"  {r[0]:<24}{r[1]:<24}{r[2]:<28}{r[3]}")
    print("\n  Catches: limits change without notice, free tiers may log or train on\n"
          "  your prompts, and rate limits break under real traffic. Fine for learning\n"
          "  and demos; for private documents prefer your own Ollama (parts 2-4).")


# ============================================================================
# PART 7: Before anything goes public -- the checklist
# ============================================================================

def part7_checklist():
    header("PART 7 -- Checklist before it goes public")
    for c in ["Require an API key (--key); share it privately, rotate it if leaked",
              "Never expose Ollama's :11434 itself -- it has no auth; expose only /ask",
              "Cap input size and answer length (413 / 500-char limit / num_predict)",
              "Rate-limit per caller (a tunnel or Cloudflare rule) -- free CPUs are slow",
              "Keep 'answer only from documents, else I don't know' (lesson 16 part 4)",
              "Log questions + sources, not secrets, to debug bad answers (lesson 06)",
              "Private docs + free API tier = your data on someone else's servers",
              "GET /health in a free uptime monitor to know when it's down"]:
        print("   [ ]", c)
    print("\n  Verdict: laptop + /ask + tunnel is a free demo in 5 minutes; an Oracle\n"
          "  Always Free VM is a free 24/7 service for small models.")


def serve(host: str, port: int, model: str, key: str | None):
    if host not in ("127.0.0.1", "localhost") and not key:
        raise SystemExit("refusing to listen on a public address without --key")
    print(f"  /ask API on http://{host}:{port}  model={model}  key={'set' if key else 'NONE (local only)'}")
    print(f"  Ollama: {'running' if lesson16.ollama_up() else 'NOT running -- answers will be 503'}   (Ctrl+C to stop)")
    ThreadingHTTPServer((host, port), make_handler(model, key)).serve_forever()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="run the /ask API (step 1)")
    ap.add_argument("--host", default="127.0.0.1", help="0.0.0.0 to accept other machines (needs --key)")
    ap.add_argument("--port", type=int, default=8017)
    ap.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model tag (lesson 15)")
    ap.add_argument("--key", default=os.environ.get("API_KEY"), help="required X-API-Key (or env API_KEY)")
    args = ap.parse_args()
    if args.serve:
        return serve(args.host, args.port, args.model, args.key)
    part1_map()
    part2_self_test(args.model)
    part3_tunnel()
    part4_host()
    part5_publish()
    part6_free_apis()
    part7_checklist()


if __name__ == "__main__":
    main()

# Key takeaway: deploying = your RAG code behind an /ask endpoint + a place for
# Ollama to run + a URL. All three have free options; the API key is not optional.
# Exercise: run --serve, open a cloudflared tunnel, and call /ask from your phone.
