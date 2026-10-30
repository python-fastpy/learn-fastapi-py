"""07 -- Tool calling  (simple version)
=====================================

IN ONE LINE:
  The model can't run code. It can only ASK you to run a tool.
  Your code runs it and sends the result back. Then the model answers.

REAL USE CASE:
  User asks your FastAPI bot: "What is the weather in Paris?"
  The model doesn't know today's weather, but you gave it a tool.

  ┌──────────────┐  POST /chat  ┌──────────────────────┐  tools=[...]  ┌──────────────────────┐
  │   Browser    │ ───────────▶ │    YOUR FASTAPI      │ ────────────▶ │     LLM PROVIDER     │
  │ "weather in  │              │ the tool LOOP runs   │               │ decides: answer now, │
  │  Paris?"     │ ◀─────────── │ here (THIS LESSON)   │ ◀──────────── │ or ask for a tool    │
  └──────────────┘ "It is 18 C" └──────────────────────┘   tool_use    └──────────────────────┘
                                     │            ▲
            get_weather(city="Paris")│            │{"city": "Paris", "temp_c": 18}
                                     ▼            │
                                ┌──────────────────────┐
                                │ TOOL = your function │
                                │ (DB, weather API...) │
                                └──────────────────────┘
  The LLM never talks to the tool. Only YOUR code does.

IN SHORT:

     YOUR CODE                                   MODEL
     question + tool list  ───────────────────▶
                           ◀───────────────────  "please call get_weather(Paris)"
     run get_weather("Paris") -> {"temp": 18}
     tool result           ───────────────────▶
                           ◀───────────────────  "It is 18 C in Paris."  (done)

THE FULL TOOL LOOP, message by message (the real run of STEP 3 in the output):

    USER                YOUR FASTAPI CODE                        LLM                                TOOL
    (you)               (chat + run_tool)                   (fake_model)                        (get_weather)
      │                         │                                 │                                   │
      │ "What is the weather    │                                 │                                   │
      │  in Paris?"             │                                 │                                   │
      │────────────────────────▶│                                 │                                   │
      │                         │ turn 1: send 1 message          │                                   │
      │                         │ + tools=[WEATHER_TOOL]          │                                   │
      │                         │────────────────────────────────▶│                                   │
      │                         │                                 │ reads the question and the        │
      │                         │                                 │ tool description. Decides:        │
      │                         │                                 │ "I need get_weather"              │
      │                         │ tool_use: get_weather           │                                   │
      │                         │   input {'city': 'Paris'}       │                                   │
      │                         │◀────────────────────────────────│                                   │
      │                         │ run_tool: name ok, "city" ok    │                                   │
      │                         │                                 │ get_weather(city="Paris")         │
      │                         │────────────────────────────────────────────────────────────────────▶│
      │                         │                                 │ {"city": "Paris", "temp_c": 18}   │
      │                         │◀────────────────────────────────────────────────────────────────────│
      │                         │ json text = the tool_result     │                                   │
      │                         │ turn 2: send 3 messages         │                                   │
      │                         │ (last one = tool_result)        │                                   │
      │                         │────────────────────────────────▶│                                   │
      │                         │                                 │ reads the tool_result             │
      │                         │ text: "It is 18 C in Paris."    │                                   │
      │                         │◀────────────────────────────────│                                   │
      │                         │ type == "text" -> stop loop     │                                   │
      │ "It is 18 C in Paris."  │                                 │                                   │
      │◀────────────────────────│                                 │                                   │
      │                         │                                 │                                   │

  Two calls to the LLM for one question. Each call sends the WHOLE message list again.

BOTH RUNS, step by step (STEP 3 and STEP 4 in the output):

   question       turn   sent    model replies                      your code ran the tool
   ────────────   ────   ─────   ────────────────────────────────   ─────────────────────────────────
   ... Paris?     1      1 msg   tool_use {'city': 'Paris'}         {"city": "Paris", "temp_c": 18}
                  2      3 msg   text "It is 18 C in Paris."        (none -> loop ends)
   ... Atlantis?  1      1 msg   tool_use {'city': 'Atlantis'}      error: unknown city: Atlantis
                  2      3 msg   text "Sorry, I could not get the   (none -> loop ends)
                                 weather (error: unknown city:
                                 Atlantis)."

   The tool failed, but the app did NOT crash. The error went back as a normal
   tool_result. The model read it and explained the problem to the user.

WHAT AN ENGINEER MUST KNOW:
  1. A tool = your normal function + a definition (name, description, input schema).
  2. The model picks the tool by reading the DESCRIPTION. Write it well.
  3. YOUR code runs the tool. Check the arguments; the model can get them wrong.
  4. If the tool fails, send the error back as a result. The model can fix it.
  5. It's a loop: keep going until the model answers with text, not a tool call.

Run:  uv run python simple/07_tool_calling.py
"""

import json

# ----------------------------------------------------------------------------
# STEP 1: the tool = a normal function + a definition the model can read
# ----------------------------------------------------------------------------
#   YOUR PYTHON FUNCTION                       THE DEFINITION (sent to the model)
#   ┌───────────────────────────────┐          ┌──────────────────────────────────────────────┐
#   │ def get_weather(city):        │          │ name:         "get_weather"                  │
#   │   "paris"  -> 18              │  same    │ description:  "Get the current temperature   │
#   │   "london" -> 12              │ ◀──────▶ │                for a city. Use for any       │
#   │   other    -> ValueError      │  name    │                weather question."            │
#   └───────────────────────────────┘          │ input_schema: needs ['city'] (a string)      │
#          ▲                                   └──────────────────────────────────────────────┘
#          │                                                         │
#   TOOLS = {"get_weather": get_weather}                             ▼
#   (name -> function, used by run_tool)       the model ONLY sees this box, never your code
def get_weather(city):
    fake_data = {"paris": 18, "london": 12}
    if city.lower() not in fake_data:
        raise ValueError("unknown city: " + city)
    return {"city": city, "temp_c": fake_data[city.lower()]}


# This is the real shape you send in the API call (Anthropic: tools=[...]).
WEATHER_TOOL = {
    "name": "get_weather",
    "description": "Get the current temperature for a city. Use for any weather question.",
    "input_schema": {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "City name, e.g. Paris"}},
        "required": ["city"],
    },
}

TOOLS = {"get_weather": get_weather}                # name -> the Python function


# ----------------------------------------------------------------------------
# STEP 2: run the tool safely. Errors become a RESULT, not a crash.
# ----------------------------------------------------------------------------
#   run_tool("get_weather", {"city": "Paris"})
#      │
#      ▼
#   name in TOOLS? ── no ──▶ "error: no tool named ..."
#      │ yes
#      ▼
#   "city" in args? ── no ──▶ "error: missing argument 'city'"      ◀── run_tool(..., {})
#      │ yes
#      ▼
#   get_weather(city=...) raises? ── yes ──▶ "error: unknown city: Atlantis"   ◀── STEP 4
#      │ no
#      ▼
#   {"city": "Paris", "temp_c": 18}   (a Python dict)
#      │
#      ▼  json.dumps(...)   tool results are sent as TEXT
#   '{"city": "Paris", "temp_c": 18}'
#
#   Every path returns a string. Nothing raises. The loop never crashes.
def run_tool(name, args):
    if name not in TOOLS:
        return "error: no tool named " + name
    if "city" not in args:                          # check the model's arguments
        return "error: missing argument 'city'"
    try:
        result = TOOLS[name](**args)                # **args -> get_weather(city="Paris")
        return json.dumps(result)                   # tool results are sent as TEXT
    except Exception as error:
        return "error: " + str(error)               # the model reads this and can retry


# ----------------------------------------------------------------------------
# STEP 3: a fake model (so this runs without an API key)
# ----------------------------------------------------------------------------
#   messages (the whole list)
#      │
#      ▼  look at the LAST message only
#   is it the user's question?  ── yes ──▶ "paris" in it?  ── yes ──▶ tool_use {'city': 'Paris'}
#   (role "user", no "type")                  │ no
#      │ no, it is a tool_result              └──────────────────────▶ tool_use {'city': 'Atlantis'}
#      ▼
#   result starts with "error"? ── yes ──▶ text "Sorry, I could not get the weather (error: ...)."
#      │ no
#      ▼
#   json.loads('{"city": "Paris", "temp_c": 18}') ──▶ text "It is 18 C in Paris."
#
# A real model makes this choice itself, by reading the tool description.
# Real call (Anthropic SDK):
#   reply = client.messages.create(model="claude-...", max_tokens=500,
#                                  tools=[WEATHER_TOOL], messages=messages)
#   if reply.stop_reason == "tool_use": ... find the block with type "tool_use"
def fake_model(messages):
    last = messages[-1]
    if last["role"] == "user" and "type" not in last:
        # First turn: the model sees a weather question and asks for the tool.
        city = "Paris" if "paris" in last["content"].lower() else "Atlantis"
        return {"type": "tool_use", "name": "get_weather", "input": {"city": city}}
    # Later turn: the model reads the tool result and writes the answer.
    result = last["content"]
    if result.startswith("error"):
        return {"type": "text", "text": "Sorry, I could not get the weather (" + result + ")."}
    data = json.loads(result)
    return {"type": "text", "text": "It is " + str(data["temp_c"]) + " C in " + data["city"] + "."}


# ----------------------------------------------------------------------------
# STEP 4: THE LOOP = ask model -> run tool -> send result -> repeat
# ----------------------------------------------------------------------------
#   messages = [user "What is the weather in Paris?"]
#      │
#      ▼
#   ┌─▶ turn 1..5: send ALL messages to the model     (turn 1: 1 message, turn 2: 3 messages)
#   │      │
#   │      ▼
#   │   reply = fake_model(messages)
#   │   messages.append(assistant reply)
#   │      │
#   │      ▼
#   │   reply type is "text"? ── yes ──▶ END: return "It is 18 C in Paris."
#   │      │ no, it is "tool_use"
#   │      ▼
#   │   result = run_tool("get_weather", {'city': 'Paris'})
#   │          ──▶ '{"city": "Paris", "temp_c": 18}'
#   │      │
#   │      ▼
#   │   messages.append(user tool_result)
#   │      │
#   │      ▼
#   │   was that turn 5? ── yes ──▶ END: "stopped: too many turns"  (safety limit)
#   │      │ no
#   └──────┘
#
#   The messages list sent in turn 2 (3 messages):
#   [0] user       "What is the weather in Paris?"
#   [1] assistant  tool_use get_weather {'city': 'Paris'}
#   [2] user       tool_result '{"city": "Paris", "temp_c": 18}'
def chat(question):
    messages = [{"role": "user", "content": question}]
    for turn in range(1, 6):                        # max 5 turns, so it can't loop forever
        print("   turn", turn, "send", len(messages), "message(s) to the model")
        reply = fake_model(messages)
        messages.append({"role": "assistant", "content": reply})
        if reply["type"] == "text":                 # no tool needed -> we are done
            print("   turn", turn, "model answers:", reply["text"])
            return reply["text"]
        print("   turn", turn, "model asks for tool:", reply["name"], reply["input"])
        result = run_tool(reply["name"], reply["input"])
        print("   turn", turn, "your code ran it  ->", result)
        # Send the result back. (Anthropic puts it in a "user" message as "tool_result".)
        messages.append({"role": "user", "type": "tool_result", "content": result})
    return "stopped: too many turns"


def main():
    print("STEP 1: the tool definition the model sees")
    print("   name       :", WEATHER_TOOL["name"])
    print("   description:", WEATHER_TOOL["description"])
    print("   needs      :", WEATHER_TOOL["input_schema"]["required"])

    print("\nSTEP 2: run the tool by hand (good and bad input)")
    print("   run_tool('get_weather', {'city': 'Paris'})  ->", run_tool("get_weather", {"city": "Paris"}))
    print("   run_tool('get_weather', {})                 ->", run_tool("get_weather", {}))

    print("\nSTEP 3: the full loop, happy path")
    chat("What is the weather in Paris?")

    print("\nSTEP 4: the full loop, tool fails (no crash, model explains)")
    chat("What is the weather in Atlantis?")


if __name__ == "__main__":
    main()

# Remember:
#   - The model only ASKS. Your code runs the tool.
#   - Good name + description = the model picks the right tool.
#   - Return errors as results, never crash the loop.
#   - Always set a max number of turns.
#   - Tools that change things (delete, pay, email) need user confirmation.
# Try: ask "What is the weather in London?". Then change fake_model so it
#      picks London too (hint: look at how it picks "Paris").
