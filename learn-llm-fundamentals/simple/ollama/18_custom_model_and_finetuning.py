"""18 -- Custom model vs fine-tuning: when to change the MODEL, not the prompt
=============================================================================

CONCEPT IN ONE LINE:
  Most problems are solved with a better PROMPT or RAG. Fine-tuning (changing the
  model's weights) is for teaching a STYLE or FORMAT, not facts. (details: simple/14, simple/16)

   WHAT DO YOU NEED?
     new FACTS / your documents ─────────▶ RAG                    (lessons 14, 15)
     fixed rules, persona, settings ─────▶ custom model / prompt  (THIS lesson, step 1)
     a style or format the prompt can't ─▶ fine-tuning            (step 3: how it works)
     get right, thousands of examples

  CUSTOM MODEL in Ollama (a "Modelfile") = base model + baked-in system prompt + settings.
  The weights do NOT change. It is just a saved, named configuration:

     llama3.2  +  system "You are Acme's support bot..."  +  temperature 0
         └──────────────────────┬───────────────────────────────────────┘
                                ▼
                         "acme-support"   (shows up in `ollama list`)

  FINE-TUNING = the weights DO change:
     examples.jsonl ──▶ train a LoRA adapter (free GPU: Google Colab + Unsloth)
     (1000+ Q/A pairs)          │
                                ▼
                     export as GGUF file ──▶ ollama create my-model -f Modelfile  (FROM ./my-model.gguf)
"""

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"

SYSTEM = ("You are Acme's support bot. Always answer in at most 2 sentences, "
          "be friendly, and end every answer with 'Anything else?'")
QUESTION = [{"role": "user", "content": "How do I reset my password?"}]   # no system message!


def post(path, body):
    """Send JSON to Ollama (e.g. /api/create, /api/chat), return the JSON answer."""
    resp = httpx.post(OLLAMA + path, json=body, timeout=300)   # json= sends body as JSON
    resp.raise_for_status()                                # 4xx/5xx -> exception
    return resp.json()


def main():
    print("STEP 1: create a custom model 'acme-support' from llama3.2")
    r = post("/api/create", {"model": "acme-support", "from": CHAT_MODEL, "system": SYSTEM,
                             "parameters": {"temperature": 0}, "stream": False})
    print("   status:", r.get("status"))
    print("   (same as a Modelfile:  FROM llama3.2 / SYSTEM \"...\" / PARAMETER temperature 0)")

    print("\nSTEP 2: same question to both models -- our request has NO system prompt")
    for model in ("acme-support", CHAT_MODEL):
        r = post("/api/chat", {"model": model, "messages": QUESTION, "stream": False,
                               "options": {"num_predict": 80}})
        print(f"   {model:<13}: {r['message']['content'].strip()[:200]}")
    print("   -> acme-support follows the baked-in rules; plain llama3.2 does not know them.")

    print("\nSTEP 3: what fine-tuning would add (not run here -- it needs a GPU and data)")
    print("   prompt / custom model : rules in words. Easy, instant, free. Try this FIRST.")
    print("   RAG                   : gives the model YOUR facts at question time.")
    print("   fine-tuning           : learns from 1000s of examples; good for tone/format;")
    print("                           bad for facts (they get stale and it still hallucinates).")

    print("\nCLEAN UP when done:  ollama rm acme-support")


if __name__ == "__main__":
    main()

# Try: change SYSTEM to make the bot answer only in German, run again, then `ollama run acme-support`.
