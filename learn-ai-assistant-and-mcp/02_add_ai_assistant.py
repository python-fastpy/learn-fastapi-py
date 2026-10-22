"""Step 2 -- Add an AI assistant on top of the app
=====================================================

Same `reading_list.py` as step 1, completely unchanged. What's new is a
LOOP: describe the four functions to a real model as tools, let it decide
which to call from a plain-English request, run the one it picked, and
hand the result back so it can answer in words.

    "add Dune by Frank Herbert, then show me my list"
         │
         ▼
    ┌──────────────────────── THE AGENT LOOP ────────────────────────┐
    │  while True:                                                   │
    │      message = call_llm(messages, tools=TOOL_SCHEMAS)          │
    │      if no tool_calls: print the final answer, stop            │
    │      else: run reading_list.<name>(**arguments), add result    │
    │            to messages, loop again                             │
    └──────────────────────────────────────────────────────────────────┘

This is the SAME loop shape as learn-agents/01 and /08 -- if you've
already done that project, nothing here is new mechanically. What's new
is the app: a real, tiny CRUD app instead of greet/translate.

Needs the same .env as learn-agents (TR Orchestrator credentials) --
copy .env.example to .env and fill them in, or run llm_client.py directly
first to confirm the connection.

Run:  uv run python 02_add_ai_assistant.py
"""

import json
import os

from dotenv import load_dotenv

import reading_list
from reading_list import add_book, list_books, mark_status, remove_book

load_dotenv()

TOOLS = {
    "add_book": add_book,
    "list_books": list_books,
    "mark_status": mark_status,
    "remove_book": remove_book,
}

# Hand-written schemas (lesson 02 of learn-agents shows how to GENERATE
# these from a function's signature instead of writing them by hand --
# step 3 of THIS project does that automatically, via MCP).
TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "add_book", "description": "Add a book to the reading list.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "author": {"type": "string"}},
            "required": ["title", "author"]}}},
    {"type": "function", "function": {
        "name": "list_books", "description": "List books, optionally filtered by status.",
        "parameters": {"type": "object", "properties": {
            "status": {"type": "string", "description": "to_read, reading, or read"}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "mark_status", "description": "Change a book's status.",
        "parameters": {"type": "object", "properties": {
            "book_id": {"type": "integer"},
            "status": {"type": "string", "description": "to_read, reading, or read"}},
            "required": ["book_id", "status"]}}},
    {"type": "function", "function": {
        "name": "remove_book", "description": "Remove a book from the list.",
        "parameters": {"type": "object", "properties": {"book_id": {"type": "integer"}},
            "required": ["book_id"]}}},
]


def run_assistant(request: str, max_steps: int = 6) -> str:
    from llm_client import call_llm   # deferred so --help works without a live connection

    print(f"you: {request!r}")
    messages: list[dict] = [{"role": "user", "content": request}]

    for _ in range(max_steps):
        message = call_llm(messages, tools=TOOL_SCHEMAS)

        if not message.get("tool_calls"):
            print(f"assistant: {message['content']}")
            return message["content"]

        messages.append(message)
        for call in message["tool_calls"]:
            name = call["function"]["name"]
            arguments = json.loads(call["function"]["arguments"])
            result = TOOLS[name](**arguments)
            print(f"  [called] {name}({arguments}) -> {result}")
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})

    raise RuntimeError(f"no final answer after {max_steps} steps")


if __name__ == "__main__":
    if not os.getenv("LEON_ORCHESTRATOR_API_KEY"):
        print("No .env found -- copy .env.example to .env and fill in credentials to run this.")
    else:
        run_assistant("Add 'Dune' by Frank Herbert, then list everything on my reading list.")
        reading_list.BOOKS.clear()   # reset for a second, independent example
        reading_list._next_id = 1
        print()
        run_assistant("Add 'Klara and the Sun' by Kazuo Ishiguro, mark it as reading, then confirm.")

# Example output (wording varies -- the model is not deterministic -- but
# the tool-call sequence should match):
#
# you: "Add 'Dune' by Frank Herbert, then list everything on my reading list."
#   [called] add_book({'title': 'Dune', 'author': 'Frank Herbert'}) -> {'id': 1, ...}
#   [called] list_books({}) -> [{'id': 1, 'title': 'Dune', ...}]
# assistant: I've added "Dune" by Frank Herbert. Here's your reading list: ...
