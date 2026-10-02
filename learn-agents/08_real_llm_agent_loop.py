"""Lesson 08 -- The SAME agent loop, with a real LLM instead of the mock
=============================================================================

Lesson 01 built the agent loop and said: swapping `decide()` for a real
model call is a one-line change, nothing else moves. This lesson is that
swap, proven -- same loop shape, same tools, a real model now makes every
decision instead of a hand-written if/else.

    lesson 01                              THIS lesson
    decision = decide(messages, request)   message = call_llm(messages, tools=SCHEMAS)
    if isinstance(decision, FinalAnswer):  if not message.get("tool_calls"):
        return decision.text                   return message["content"]
    result = TOOLS[decision.name](...)     for call in message["tool_calls"]:
    messages.append(...)                       result = TOOLS[name](**args)
    # loop                                      messages.append(tool result)
                                            # loop -- identical shape

`call_llm()` is raw HTTP (see llm_client.py) -- no SDK, no agent
framework. The tool SCHEMAS are the OpenAI/Azure tool-calling shape
(lesson 02 built the same idea in a simpler, flatter form).

ONE REAL DIFFERENCE from every earlier lesson: the output below is NOT
deterministic. The model's exact wording will vary call to call -- what
stays constant is the SHAPE: which tools get called, in what order, with
what arguments, and that the loop still ends in a final text answer.

Requires .env with the TR Orchestrator credentials (same ones learn-mcp
uses) -- copy .env.example to .env and fill them in, or run llm_client.py
directly first to confirm the connection works.

Run:  uv run python 08_real_llm_agent_loop.py
"""

import json
import os

from dotenv import load_dotenv

from tools import TOOLS

load_dotenv()   # so the os.getenv() check in __main__ sees .env too, not just llm_client's own call

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "greet",
            "description": "Greets someone by name.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate",
            "description": "Translates text into another language.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "language": {"type": "string", "description": "a two-letter code, e.g. fr, de, es"},
                },
                "required": ["text", "language"],
            },
        },
    },
]


def run_agent(request: str, max_steps: int = 5) -> str:
    from llm_client import call_llm   # imported here so --help/import doesn't need a live connection

    print(f"user: {request!r}")
    messages: list[dict] = [{"role": "user", "content": request}]

    for step in range(1, max_steps + 1):
        message = call_llm(messages, tools=TOOL_SCHEMAS)

        if not message.get("tool_calls"):
            print(f"agent: final answer -> {message['content']!r}")
            return message["content"]

        messages.append(message)
        for call in message["tool_calls"]:
            name = call["function"]["name"]
            arguments = json.loads(call["function"]["arguments"])
            result = TOOLS[name](**arguments)
            print(f"agent: step {step} -- model called {name}({arguments}) -> {result!r}")
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": str(result)})

    raise RuntimeError(f"no final answer after {max_steps} steps")


if __name__ == "__main__":
    if not os.getenv("LEON_ORCHESTRATOR_API_KEY"):
        print("No .env found -- copy .env.example to .env and fill in credentials to run this lesson.")
    else:
        run_agent("Greet Ada, then translate the greeting into French.")

# Example output from a real run (wording WILL differ -- the model is not
# deterministic -- but the tool-call sequence and shape should match):
#
# user: 'Greet Ada, then translate the greeting into French.'
# agent: step 1 -- model called greet({'name': 'Ada'}) -> 'Hello, Ada!'
# agent: step 2 -- model called translate({'text': 'Hello, Ada!', 'language': 'fr'}) -> 'Bonjour, Ada!'
# agent: final answer -> 'Hello, Ada! In French, that would be: Bonjour, Ada!'
#
# Compare this to lesson 01's mock output for the exact same scenario --
# same two tool calls, same final translated text in there somewhere. The
# mock's decide() was standing in for exactly this.
