"""08 -- Tool calling: the model ASKS, your code RUNS the function
=================================================================

CONCEPT IN ONE LINE:
  The model cannot run code. It replies "please call get_weather(city='Paris')",
  YOUR code runs it, and you send the result back.        (details: simple/07, simple/08)

   USER            YOUR CODE                         MODEL                 TOOL
    │ "weather      │                                  │                     │
    │  in Paris?"   │                                  │                     │
    │──────────────▶│ messages + tools=[get_weather] ─▶│                     │
    │               │◀─ tool_calls: get_weather        │                     │
    │               │      {"city": "Paris"}           │                     │
    │               │─────────────── get_weather("Paris") ──────────────────▶│
    │               │◀────────────── {"temp_c": 18, "sky": "cloudy"} ────────│
    │               │ messages + tool result ─────────▶│                     │
    │               │◀─ "It is 18°C and cloudy."       │                     │
    │◀──────────────│                                  │                     │
"""

import json

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"

# 1) your real Python functions
def get_weather(city):
    fake_db = {"paris": {"temp_c": 18, "sky": "cloudy"}, "tokyo": {"temp_c": 24, "sky": "sunny"}}
    return fake_db.get(city.lower(), {"error": f"no data for {city}"})


def get_order_status(order_id):
    return {"order_id": order_id, "status": "shipped", "eta_days": 2}


FUNCTIONS = {"get_weather": get_weather, "get_order_status": get_order_status}

# 2) the DESCRIPTION the model sees (it never sees your code)
TOOLS = [
    {"type": "function", "function": {
        "name": "get_weather", "description": "Get the current weather for a city",
        "parameters": {"type": "object", "required": ["city"],
                       "properties": {"city": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "get_order_status", "description": "Get the shipping status of an order",
        "parameters": {"type": "object", "required": ["order_id"],
                       "properties": {"order_id": {"type": "string"}}}}},
]


# 3) the loop
def run(question, max_turns=5):
    messages = [{"role": "user", "content": question}]
    for turn in range(1, max_turns + 1):
        body = {
            "model": CHAT_MODEL,
            "messages": messages,
            "stream": False,
            "tools": TOOLS,                                   # the model sees only these descriptions
            "options": {"temperature": 0},
        }
        r = httpx.post(OLLAMA + "/api/chat", json=body, timeout=300).raise_for_status().json()
        msg = r["message"]
        messages.append(msg)
        if not msg.get("tool_calls"):                         # no tool wanted -> final answer
            print(f"   turn {turn}: final answer -> {msg['content']}")
            return
        for call in msg["tool_calls"]:
            name, args = call["function"]["name"], call["function"]["arguments"]
            func = FUNCTIONS.get(name)
            try:                                              # the model can send wrong args
                result = func(**args) if func else {"error": f"unknown tool {name}"}
            except TypeError as e:
                result = {"error": f"bad arguments: {e}"}     # send the error back, don't crash
            print(f"   turn {turn}: model asks {name}({args}) -> your code returns {result}")
            messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result)})
    print("   stopped: too many turns")


def main():
    for q in ["What is the weather in Paris?",
              "Where is my order A-1001?",
              "What is 2 + 2?"]:                      # no tool needed -> answers directly
        print(f"STEP: {q}")
        run(q)
        print()
    print("SAFETY: the model chooses the tool and the arguments. Check them before running,")
    print("and ask a human before tools that change things (refunds, emails, deletes).")


if __name__ == "__main__":
    main()

# Try: ask "Weather in Paris and Tokyo?" -- the model may ask for 2 tools in one turn.
