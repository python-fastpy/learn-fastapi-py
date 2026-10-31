"""04 -- The chat API: roles, no memory, and why answers get cut off
===================================================================

CONCEPT IN ONE LINE:
  You send a LIST of messages every time. The model remembers nothing between calls.
                                                                  (details: simple/03)

   call 1:  [system, user1]                          ──▶ assistant1
   call 2:  [system, user1, assistant1, user2]       ──▶ assistant2   ◀ YOU resend history
   call 3:  [system, user1, assistant1, user2, ...]  ──▶ ...          ◀ input grows every turn

   ROLES:   system    = rules from you, the developer ("You are a support bot...")
            user      = what the end user typed
            assistant = what the model said before
            tool      = a result from your code (lesson 10)

   RESPONSE: message.content   the answer
             done_reason       "stop" = finished,  "length" = CUT OFF by num_predict (max_tokens)
             prompt_eval_count / eval_count = input / output tokens (your bill)
"""

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"
SYSTEM = {"role": "system", "content": "You are a short, friendly assistant. Max 1 sentence."}
OPT = {"temperature": 0}


def chat(messages, options):
    """One call to /api/chat. Returns the full response dict."""
    body = {
        "model": CHAT_MODEL,
        "messages": messages,               # the WHOLE list, every time
        "stream": False,
        "options": options,
    }
    resp = httpx.post(OLLAMA + "/api/chat", json=body, timeout=300)
    resp.raise_for_status()
    return resp.json()


def main():
    print("STEP 1: the model has NO memory between calls")
    chat([SYSTEM, {"role": "user", "content": "My name is Priya."}], options=OPT)
    r = chat([SYSTEM, {"role": "user", "content": "What is my name?"}], options=OPT)
    print("  (separate call) What is my name? ->", r["message"]["content"])

    print("\nSTEP 2: memory = YOU send the history again")
    history = [SYSTEM]
    for text in ["My name is Priya.", "I work on a FastAPI app.", "What is my name and what do I build?"]:
        history.append({"role": "user", "content": text})
        r = chat(history, options=OPT)
        history.append(r["message"])                  # keep the answer for the next call
        print(f"  user: {text:<40} input tokens: {r['prompt_eval_count']:>4}")
        print(f"        bot:  {r['message']['content']}")
    print("  -> input tokens grow every turn: long chats cost more and fill the window.")

    print("\nSTEP 3: done_reason -- ALWAYS check it")
    question = [{"role": "user", "content": "Explain what an API is in 3 sentences."}]
    for limit in (8, 200):
        r = chat(question, options={"temperature": 0, "num_predict": limit})
        print(f"  num_predict={limit:<4} done_reason={r['done_reason']!r:<9} "
              f"text={r['message']['content'][:70]!r}")
    print("  -> 'length' means the answer was CUT OFF. In your app: raise the limit or warn the user.")


if __name__ == "__main__":
    main()

# Try: change SYSTEM to "Answer only in French." -- the system role controls behaviour.
