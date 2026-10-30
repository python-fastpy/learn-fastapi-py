"""07 -- Tool calling  (simple version)
=====================================

IN ONE LINE:
  The model can't run code. It can only ASK you to run a tool.
  Your code runs it and sends the result back. Then the model answers.

REAL USE CASE:
  User asks your FastAPI bot: "What is the weather in Paris?"
  The model doesn't know today's weather, but you gave it a tool.

     YOUR CODE                                   MODEL
     question + tool list  ───────────────────▶
                           ◀───────────────────  "please call get_weather(Paris)"
     run get_weather("Paris") -> {"temp": 18}
     tool result           ───────────────────▶
                           ◀───────────────────  "It is 18 C in Paris."  (done)

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
def chat(question):
    messages = [{"role": "user", "content": question}]
    for turn in range(1, 6):                        # max 5 turns, so it can't loop forever
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
