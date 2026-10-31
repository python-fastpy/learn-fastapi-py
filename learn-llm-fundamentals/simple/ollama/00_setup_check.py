"""00 -- Setup check: is a free open-source model running on your PC?
====================================================================

ONE-TIME SETUP (free, no account, no API key):

   1. Install Ollama          https://ollama.com/download   (Windows / Mac / Linux)
   2. Download 2 models       ollama pull llama3.2           (~2 GB, the chat model)
                              ollama pull nomic-embed-text   (~270 MB, for lesson 10 RAG)
   3. Run this file           uv run python simple/ollama/00_setup_check.py

HOW IT WORKS:

   ┌─────────────────┐   HTTP :11434   ┌───────────────────────────────┐
   │ your Python     │ ──────────────▶ │ Ollama (runs in background)   │
   │ (these lessons) │ ◀────────────── │   loads llama3.2 into RAM/GPU │
   └─────────────────┘      JSON       └───────────────────────────────┘

   Same shape as a paid API (OpenAI, Anthropic): send JSON messages, get JSON back.
   Everything you learn here works the same way with a paid model later.
"""

import json
import urllib.request

from ollama_client import CHAT_MODEL, EMBED_MODEL, OLLAMA, ask


def main():
    print("STEP 1: is Ollama running?")
    try:
        with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=5) as r:
            models = [m["name"] for m in json.loads(r.read())["models"]]
    except OSError:
        print("  NO -- install from https://ollama.com and start it.")
        return
    print("  yes. models on this PC:", models)

    print("\nSTEP 2: are the 2 models we need downloaded?")
    for need in (CHAT_MODEL, EMBED_MODEL):
        ok = any(m.split(":")[0] == need for m in models)
        print(f"  {need:<18} {'OK' if ok else 'MISSING -> run:  ollama pull ' + need}")

    print("\nSTEP 3: first question to the model (first call loads it, may take ~10 s)")
    print("  answer:", ask("Say hello in exactly 5 words.", options={"temperature": 0}))
    print("\nAll good -- go to 01_next_token.py")


if __name__ == "__main__":
    main()
