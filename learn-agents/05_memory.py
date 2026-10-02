"""Lesson 05 -- Short-term vs. long-term memory
==================================================

SHORT-TERM memory is the `messages` list lesson 01's loop built up --
it exists only for the duration of ONE run, then it's gone. LONG-TERM
memory is something that survives ACROSS separate runs -- a database, a
vector store, or (here) a plain dict standing in for one. The difference
isn't the data structure; it's WHEN it gets thrown away.

    RUN 1                                    RUN 2 (a LATER, separate call)
    messages = []        <- fresh, empty         messages = []        <- fresh again,
         │                                             │                  run 1's are GONE
         ▼                                             ▼
    "remember Ada                             "greet Ada"
     prefers french"                                │
         │                                           ▼
         ▼                                 LONG_TERM_MEMORY["Ada"]
    LONG_TERM_MEMORY["Ada"] = "fr"  ───────►   still has "fr" --
    (written here, OUTSIDE messages,            this is the only reason
     survives run 1 ending)                     run 2 can act on it

Run:  uv run python 05_memory.py
"""

from tools import greet, translate

# the stand-in for a real persistent store (a database row, a vector store
# entry keyed by user id, ...) -- note this dict is defined OUTSIDE run(),
# at module level, which is exactly what makes it survive between calls
LONG_TERM_MEMORY: dict[str, str] = {}


def run(request: str) -> str:
    """Every call starts with EMPTY short-term memory -- nothing from a
    previous run() call is visible here except through LONG_TERM_MEMORY."""
    messages: list[dict] = []   # short-term: gone the instant run() returns

    if request.startswith("remember "):
        # "remember Ada prefers french"
        _, who, _, language_word = request.split(" ", 3)
        lang_code = {"french": "fr", "german": "de"}.get(language_word, "en")
        LONG_TERM_MEMORY[who] = lang_code
        messages.append({"role": "system", "note": f"saved {who} -> {lang_code}"})
        return f"Got it -- I'll remember {who} prefers {language_word}."

    if request.startswith("greet "):
        who = request.split(" ", 1)[1].strip()
        greeting = greet(who)
        language = LONG_TERM_MEMORY.get(who)   # <- the ONLY way run 2 can know this
        if language:
            greeting = translate(greeting, language)
            messages.append({"role": "system", "note": f"found {who} -> {language} in long-term memory"})
        return greeting

    return "I don't understand that request."


if __name__ == "__main__":
    print("=== run 1: a separate, earlier call ===")
    print("user:", "remember Ada prefers french")
    print("agent:", run("remember Ada prefers french"))
    print("(run 1's short-term `messages` list is thrown away right here)")

    print("\n=== run 2: a LATER, completely separate call -- fresh messages=[] ===")
    print("user:", "greet Ada")
    print("agent:", run("greet Ada"))
    print("(run 2 never saw run 1's messages -- only LONG_TERM_MEMORY carried the fact forward)")

    print("\n=== run 3: someone run() has never heard of ===")
    print("user:", "greet Bob")
    print("agent:", run("greet Bob"), " (no long-term entry for Bob -> plain English)")

# Expected output:
#
# === run 1: a separate, earlier call ===
# user: remember Ada prefers french
# agent: Got it -- I'll remember Ada prefers french.
# (run 1's short-term `messages` list is thrown away right here)
#
# === run 2: a LATER, completely separate call -- fresh messages=[] ===
# user: greet Ada
# agent: Bonjour, Ada!
# (run 2 never saw run 1's messages -- only LONG_TERM_MEMORY carried the fact forward)
#
# === run 3: someone run() has never heard of ===
# user: greet Bob
# agent: Hello, Bob!  (no long-term entry for Bob -> plain English)
