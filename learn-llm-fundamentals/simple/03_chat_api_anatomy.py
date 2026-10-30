"""03 -- Anatomy of a chat API call  (simple version)
====================================================

IN ONE LINE:
  You send a LIST of messages with roles. The API joins them into one long
  text, the model continues it, and you get back: text + stop_reason + usage.

REAL USE CASE:
  Your FastAPI /chat endpoint. The API remembers NOTHING, so your code
  keeps the history and sends ALL of it on every call:

     user ──▶ FastAPI /chat
                 │  history = [system, user, assistant, user, ...]
                 ▼
         ┌────────────────┐
         │   LLM API      │  (joins all messages into one text)
         └────────────────┘
                 │  content, stop_reason, usage
                 ▼
     FastAPI checks stop_reason, saves the reply to history, returns it

WHERE EACH PART LIVES IN A REAL APP:

  ┌──────────────┐  POST /chat   ┌──────────────────┐  HTTPS   ┌─────────────────────────────┐
  │   Browser    │ ────────────▶ │  YOUR FASTAPI    │ ───────▶ │        LLM PROVIDER         │
  │ "What about  │  1 message    │  history (in DB):│ ALL msgs │  1. join msgs into 1 text   │
  │  food?"      │               │  system, user,   │          │  2. model writes tokens     │
  │              │               │  assistant, user │          │  3. stop: end_turn or       │
  │              │ ◀──────────── │  + save reply    │ ◀─────── │     max_tokens              │
  └──────────────┘   reply text  │  + log usage $   │  (see    │  4. count tokens = usage    │
                                 └──────────────────┘  below)  └─────────────────────────────┘
  Back from the provider: content + stop_reason + usage.
  The browser sends 1 message. Your FastAPI sends the WHOLE history.

ONE REQUEST AND ONE RESPONSE:

  REQUEST (you send)                             RESPONSE (you get back)
  ┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
  │ model, max_tokens=300                │       │ content: "Colosseum in the morning.."│
  │ messages = [                         │ ────▶ │ stop_reason: "end_turn"              │
  │   {role: system,    content: ...},   │       │ usage: {input_tokens: 25,            │
  │   {role: user,      content: ...},   │       │         output_tokens: 14}           │
  │ ]                                    │ ◀──── │                                      │
  └──────────────────────────────────────┘       └──────────────────────────────────────┘
       (turn 1 of the real run in STEP 2)

ONE FULL CHAT, step by step (the real numbers printed by STEP 2):

   turn   messages sent               input tokens   output tokens   cost of this turn
   ────   ─────────────────────────   ────────────   ─────────────   ─────────────────
   1      sys, user                   25             14              $0.000285
   2      sys, user, asst, user       50             15              $0.000375
   3      sys, + 2 old pairs, user    73             14              $0.000429
                                      ──                             ─────────
                                      input grows!                   total $0.00109

   Turn 1 sends 2 messages, turn 2 sends 4, turn 3 sends 6.
   The output stays about the same. The INPUT keeps growing.

WHAT AN ENGINEER MUST KNOW:
  1. Roles: system (your rules), user (the person), assistant (the model's old replies).
  2. The API is stateless. Every call resends the whole history, so input grows.
  3. Always check stop_reason. "max_tokens" means the answer was CUT OFF.
  4. usage tells you input and output tokens. That is your bill.
  5. Input is usually most of the cost, because history is resent every turn.

Run:  uv run python simple/03_chat_api_anatomy.py
"""

# Example prices in dollars per 1 million tokens. Output costs more per token.
PRICE_INPUT = 3.00
PRICE_OUTPUT = 15.00


# ----------------------------------------------------------------------------
# STEP 1: THE TEMPLATE = all messages become ONE text for the model
# ----------------------------------------------------------------------------
#   messages = [
#     {"role": "system", "content": "You are a helpful travel assistant. Be short."},
#     {"role": "user",   "content": "Plan a day in Rome."},
#   ]
#      │
#      ▼  for each message: "<|" + role + "|> " + content
#   "<|system|> You are a helpful travel assistant. Be short."
#   "<|user|> Plan a day in Rome."
#      │
#      ▼  add an OPEN assistant marker at the end
#   "<|assistant|> "        <- nothing after it: the model writes the next words HERE
#      │
#      ▼  join with new lines
#   one long text  ──▶  tokenizer  ──▶  model
#
#   count_tokens(text) = len(text) // 4      (about 4 characters per token)
def to_one_text(messages):
    """Wrap each message in role markers. Leave the assistant marker open."""
    lines = []
    for message in messages:
        lines.append("<|" + message["role"] + "|> " + message["content"])
    lines.append("<|assistant|> ")           # the model continues from here
    return "\n".join(lines)


def count_tokens(text):
    """Rough rule: about 4 characters per token (real APIs count exactly)."""
    return max(1, len(text) // 4)


# ----------------------------------------------------------------------------
# STEP 2: THE CALL = a fake API that returns the same shape as the real one
# ----------------------------------------------------------------------------
# The real SDK call looks like this (we do not call it here):
#   response = client.messages.create(
#       model="claude-...", max_tokens=300,
#       system="You are a travel helper.",
#       messages=[{"role": "user", "content": "Plan a day in Rome."}],
#   )
#   response.content[0].text, response.stop_reason, response.usage
#
#   fake_llm(messages, reply, max_tokens)
#      │
#      ▼
#   reply_tokens = count_tokens(reply)
#      │
#      ▼
#   reply_tokens > max_tokens? ── yes ──▶ cut reply to max_tokens x 4 characters
#      │ no                                stop_reason = "max_tokens"   (NOT complete!)
#      ▼                                          │
#   stop_reason = "end_turn"   (finished)         │
#      │◀─────────────────────────────────────────┘
#      ▼
#   return {content, stop_reason, usage: {input_tokens, output_tokens}}
#
#   real run in STEP 3:  reply needs 155 tokens, max_tokens = 20
#      ──▶ 155 > 20 ── yes ──▶ keep 20 x 4 = 80 of 620 characters, stop_reason "max_tokens"
#
#   The chat loop in main() -- YOUR code does the remembering:
#   history = [system]
#      │
#      ▼
#   ┌─▶ history.append(user question)            e.g. "What about food?"
#   │      │
#   │      ▼
#   │   fake_llm(ALL of history)  ──▶  turn 2: input 50 tokens (4 messages)
#   │      │
#   │      ▼
#   │   history.append(assistant reply)          <- skip this and the model forgets
#   │      │
#   │      ▼
#   │   total += cost(usage)
#   │      │
#   │   more turns? ── no ──▶ END (print total)
#   │      │ yes
#   └──────┘
def fake_llm(messages, reply, max_tokens=300):
    reply_tokens = count_tokens(reply)
    stop_reason = "end_turn"                 # the model finished normally
    if reply_tokens > max_tokens:
        reply = reply[: max_tokens * 4]      # cut the text, like the real API
        reply_tokens = max_tokens
        stop_reason = "max_tokens"           # the answer is NOT complete
    return {
        "content": reply,
        "stop_reason": stop_reason,
        "usage": {"input_tokens": count_tokens(to_one_text(messages)),
                  "output_tokens": reply_tokens},
    }


# ----------------------------------------------------------------------------
# STEP 3: COST = input tokens x input price + output tokens x output price
# ----------------------------------------------------------------------------
#   usage = {input_tokens: 25, output_tokens: 14}            (turn 1)
#      │
#      ▼
#   25 x $3.00   = 75     ┐
#   14 x $15.00  = 210    ├─▶ 285 / 1,000,000 = $0.000285
#                         ┘
#   Prices are per 1 MILLION tokens, so we divide by 1,000,000 at the end.
def cost(usage):
    return (usage["input_tokens"] * PRICE_INPUT
            + usage["output_tokens"] * PRICE_OUTPUT) / 1_000_000


def main():
    history = [{"role": "system", "content": "You are a helpful travel assistant. Be short."}]
    history.append({"role": "user", "content": "Plan a day in Rome."})

    print("STEP 1: what the model really sees (one text)")
    print(to_one_text(history))

    print("\nSTEP 2: a chat with 3 turns (history is resent every time)")
    turns = [
        ("Plan a day in Rome.", "Colosseum in the morning, lunch in Monti, sunset at Pincio."),
        ("What about food?", "Try cacio e pepe in Trastevere and suppli from a street stall."),
        ("Budget?", "Around 80 to 120 euros per person, with tickets and meals."),
    ]
    history = history[:1]                    # start again with only the system message
    total = 0.0
    for number, (question, answer) in enumerate(turns, start=1):
        history.append({"role": "user", "content": question})
        messages_sent = len(history)
        response = fake_llm(history, answer)
        history.append({"role": "assistant", "content": response["content"]})  # YOU save it
        total += cost(response["usage"])
        print("  turn", number, ":", messages_sent, "messages sent, input",
              response["usage"]["input_tokens"], "tokens, output",
              response["usage"]["output_tokens"], "tokens, cost $" + format(cost(response["usage"]), ".6f"))
    print("  Input grows every turn, because the whole history is sent again.")
    print("  Total cost for 3 turns: $" + format(total, ".5f"))

    print("\nSTEP 3: always check stop_reason")
    long_reply = "A very long answer about Rome. " * 20
    print("  the reply needs", count_tokens(long_reply), "tokens, but max_tokens is 20")
    response = fake_llm(history, long_reply, max_tokens=20)
    print("  stop_reason:", response["stop_reason"])
    print("  we only got", len(response["content"]), "of", len(long_reply), "characters")
    if response["stop_reason"] == "max_tokens":
        print("  The answer was CUT OFF. Raise max_tokens or ask the model to continue.")
    print("  Other values: end_turn (done), tool_use (run a tool), stop_sequence")

    print("\nSTEP 4: where the money goes (one long chat turn)")
    usage = {"input_tokens": 40_000, "output_tokens": 200}
    print("  input  40000 tokens = $" + format(40_000 * PRICE_INPUT / 1_000_000, ".3f"))
    print("  output   200 tokens = $" + format(200 * PRICE_OUTPUT / 1_000_000, ".3f"))
    print("  total               = $" + format(cost(usage), ".3f"))
    print("  Output is 5x more per token, but input is much bigger. Send less history.")


if __name__ == "__main__":
    main()

# Remember:
#   - messages = list of {role, content}. The API joins them into one text.
#   - The API has no memory. Your code keeps and resends the history.
#   - Read content, stop_reason AND usage from every response.
# Try: add 5 more turns to `turns`. How fast does the input token count grow?
