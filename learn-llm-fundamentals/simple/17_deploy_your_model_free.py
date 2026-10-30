"""17 -- Deploy your model for free  (simple version)
====================================================

IN ONE LINE:
  Deploy = put your "model + documents" code behind a URL (POST /ask),
  protect it with an API key, and run it somewhere. All of it can be free.

REAL USE CASE:
  Your handbook bot (lesson 16) works on your laptop. Now a colleague
  wants to call it from their app:

     colleague's app
          │  POST https://<your-url>/ask   {"question": "..."}  + X-API-Key
          ▼
     ┌────────────────────────────────────────────┐
     │ YOUR API (FastAPI)                         │
     │  1. check API key     -> 401 if wrong      │
     │  2. check the body    -> 400 if bad        │
     │  3. find handbook lines + build prompt     │
     │  4. ask Ollama on localhost (never public) │
     └────────────────────────────────────────────┘
          │
          ▼
     {"answer": "...", "sources": ["leave-1"]}

WHAT AN ENGINEER MUST KNOW:
  1. Only expose YOUR /ask API. Never expose Ollama's port 11434 (it has no login).
  2. Always require an API key. A public URL will be found by strangers.
  3. Limit input size and answer length. Free machines are slow and small.
  4. Free options: a tunnel from your laptop (demo), Oracle Always Free VM
     (24/7), Hugging Face Spaces (public demo), or a free API tier.
  5. Free tiers change often, and some may use your data. Read the terms.

Run:  uv run python simple/17_deploy_your_model_free.py
"""

import hmac

API_KEY = "demo-key"          # in real life: read it from an environment variable
HANDBOOK = {
    "leave-1": "full-time employees get 25 vacation days per year",
    "remote-1": "employees may work remotely up to 3 days per week",
}


# ----------------------------------------------------------------------------
# STEP 1: CHECK the request (key first, then the body)
# ----------------------------------------------------------------------------
def check_request(headers, body):
    """Return None if OK, or (status_code, error) to send back."""
    sent_key = headers.get("X-API-Key", "")
    # compare_digest takes the same time for any input, so attackers can't guess by timing
    if not hmac.compare_digest(sent_key, API_KEY):
        return 401, "missing or wrong X-API-Key"
    question = body.get("question", "")
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
        return 400, "send JSON like {\"question\": \"...\"} (1-500 characters)"
    return None


# ----------------------------------------------------------------------------
# STEP 2: ANSWER = the /ask endpoint (retrieve + ask the model)
# ----------------------------------------------------------------------------
def find_sources(question):
    """Simple search: keep lines that share an important word with the question."""
    important = set(question.lower().strip("?").split()) - {"how", "much", "do", "i", "get", "what", "about"}
    return [doc_id for doc_id, text in HANDBOOK.items() if important & set(text.split())]


def fake_model(question, sources):
    """Stand-in for Ollama, so this file runs without a server."""
    if not sources:
        return "I don't know based on the handbook."
    return f"{HANDBOOK[sources[0]]} [{sources[0]}]"


def handle_ask(headers, body):
    problem = check_request(headers, body)
    if problem:
        status, error = problem
        return status, {"error": error}
    question = body["question"]
    sources = find_sources(question)
    return 200, {"answer": fake_model(question, sources), "sources": sources}


def main():
    print("STEP 1 + 2: call our /ask endpoint (simulated, no server)")
    tests = [
        ("no key", {}, {"question": "How much vacation do I get?"}),
        ("bad body", {"X-API-Key": API_KEY}, {"q": "oops"}),
        ("good call", {"X-API-Key": API_KEY}, {"question": "How much vacation do I get?"}),
        ("not in docs", {"X-API-Key": API_KEY}, {"question": "What about parking?"}),
    ]
    for label, headers, body in tests:
        status, response = handle_ask(headers, body)
        print(f"  {label:<12} -> {status}  {response}")

    print("\nSTEP 3: where to run it for free")
    options = [
        ("laptop + tunnel", "only while your PC is on", "quick demo"),
        ("Oracle Always Free VM", "24/7, 24 GB RAM, no GPU", "small real service"),
        ("Hugging Face Space", "sleeps when idle", "public demo, tiny models"),
        ("free API tier (Groq...)", "rate limits", "no hosting at all"),
    ]
    for name, limits, best_for in options:
        print(f"  {name:<24} {limits:<26} {best_for}")


if __name__ == "__main__":
    main()

# HOW TO DO IT FOR REAL (needs: fastapi, uvicorn, Ollama; not run here):
#   from fastapi import FastAPI, Header, HTTPException
#   app = FastAPI()
#   @app.post("/ask")
#   def ask(body: dict, x_api_key: str = Header("")):
#       status_and_data = handle_ask({"X-API-Key": x_api_key}, body)
#       if status_and_data[0] != 200:
#           raise HTTPException(status_and_data[0], status_and_data[1]["error"])
#       return status_and_data[1]      # replace fake_model with a real Ollama call
#   Run:     uvicorn myapp:app --port 8017
#   Share:   cloudflared tunnel --url http://localhost:8017   (free public HTTPS URL)

# Remember:
#   - Deploy = /ask API + a place to run the model + a URL.
#   - API key and input limits are not optional.
#   - Expose only your API, never Ollama itself.
# Try: add a test that sends a 600-character question. Which status do you get?
