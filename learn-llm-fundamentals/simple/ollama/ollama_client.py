"""Tiny helper to talk to Ollama -- used by every lesson in this folder.

Ollama runs an open-source model on YOUR PC and gives it an HTTP API:

   your Python ──HTTP POST JSON──▶ http://localhost:11434/api/chat ──▶ model (llama3.2)
               ◀──────── JSON answer + token counts ─────────────────┘

It is the same idea as calling OpenAI / Anthropic, only free and local.
No packages needed: we use urllib from the standard library.
"""

import json
import sys
import urllib.error
import urllib.request

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"            # 3B model, ~2 GB, supports tools.   ollama pull llama3.2
EMBED_MODEL = "nomic-embed-text"   # turns text into vectors (lesson 10). ollama pull nomic-embed-text


def post(path, body):
    """Send JSON to Ollama, return the JSON answer."""
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:            # e.g. model not pulled yet
        sys.exit(f"Ollama error {e.code}: {e.read().decode()}\n"
                 f"Did you run:  ollama pull {body.get('model')} ?")
    except urllib.error.URLError:
        sys.exit("Cannot reach Ollama at http://localhost:11434\n"
                 "Install it from https://ollama.com and make sure it is running.")


def chat(messages, **extra):
    """One call to /api/chat. Returns the full response dict.

    messages = [{"role": "system"|"user"|"assistant"|"tool", "content": "..."}]
    extra    = options={...}, tools=[...], format={...}, logprobs=True, ...
    """
    return post("/api/chat", {"model": CHAT_MODEL, "messages": messages, "stream": False, **extra})


def ask(question, system=None, **extra):
    """Shortcut: one question in, answer text out."""
    messages = [{"role": "system", "content": system}] if system else []
    messages.append({"role": "user", "content": question})
    return chat(messages, **extra)["message"]["content"].strip()


def embed(texts):
    """Text(s) -> list of vectors (each vector = a list of numbers)."""
    return post("/api/embed", {"model": EMBED_MODEL, "input": texts})["embeddings"]
