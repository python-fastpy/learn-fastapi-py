"""00 -- Setup check: is a free open-source model running on your PC?
====================================================================

ONE-TIME SETUP (free, no account, no API key):

   1. Install Ollama          https://ollama.com/download   (Windows / Mac / Linux)
   2. Download 2 models       ollama pull llama3.2           (~2 GB, the chat model)
                              ollama pull nomic-embed-text   (~270 MB, for lessons 14-15 RAG)
   3. Run this file           uv run python simple/ollama/00_setup_check.py

OR CHECK BY HAND (same 3 steps, no Python needed):

   STEP 1 + 2   ollama list
                -> error            = Ollama is not running, start it
                -> list of models   = running; look for llama3.2 and nomic-embed-text
                                      (missing? ollama pull <name>)

   STEP 3       ollama run llama3.2 "Say hello in exactly 5 words."
                -> a short greeting = all good

   Same STEP 3 over the HTTP API the lessons use (PowerShell):

                Invoke-RestMethod http://localhost:11434/api/chat -Method Post `
                  -ContentType "application/json" `
                  -Body '{"model":"llama3.2","stream":false,
                          "messages":[{"role":"user","content":"Say hello in exactly 5 words."}]}'

START / STOP OLLAMA:

   Windows   start   open "Ollama" from the Start menu (runs in the tray, starts with Windows)
                     or in a terminal:  ollama serve   (stays running until Ctrl+C)
             stop    right-click the tray icon -> Quit Ollama
                     or:  Stop-Process -Name "ollama*"     (kills the app + server)
             check   Get-Process ollama* -ErrorAction SilentlyContinue
                     -> prints nothing = Ollama is stopped

   Mac       start   open the Ollama app        stop   menu bar icon -> Quit Ollama
   Linux     start   sudo systemctl start ollama
             stop    sudo systemctl stop ollama

   Free RAM without stopping the server:
             ollama ps                   which models are loaded in memory right now
             ollama stop llama3.2        unload that model (server keeps running)

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

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"
EMBED_MODEL = "nomic-embed-text"


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
        ok = any(m.split(":")[0] == need for m in models)    # "llama3.2:latest" counts as "llama3.2"
        print(f"  {need:<18} {'OK' if ok else 'MISSING -> run:  ollama pull ' + need}")

    print("\nSTEP 3: first question to the model (first call loads it, may take ~10 s)")
    body = {
        "model": CHAT_MODEL,
        "messages": [{"role": "user", "content": "Say hello in exactly 5 words."}],
        "stream": False,                    # one JSON answer, not a stream of chunks
        "options": {"temperature": 0},
    }
    req = urllib.request.Request(OLLAMA + "/api/chat", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        answer = json.loads(r.read())["message"]["content"].strip()
    print("  answer:", answer)
    print("\nAll good -- go to 01_next_token.py")

    print("\nWhen you are done:")
    print(f"  ollama stop {CHAT_MODEL:<16} unload the model, free RAM (server keeps running)")
    print('  Stop-Process -Name "ollama*"  stop Ollama completely (Windows)')


if __name__ == "__main__":
    main()
