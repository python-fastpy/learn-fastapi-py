"""Lesson 01 -- The Agent Loop: what Claude Code actually is
==============================================================

WHY THIS MATTERS:
  Claude Code, Cursor, and every other "AI coding agent" look magical
  from the outside. They aren't. Strip away the UI and each one is the
  same ~30-line loop:

      1. Send the conversation + a list of available tools to a model
      2. The model replies with either TEXT (it's done) or TOOL CALLS
      3. If tool calls: run them, append the results to the conversation
      4. Go back to step 1

  That's it. The model never executes anything itself -- it just emits
  the *name* of a tool and some JSON arguments. YOUR code decides whether
  to run it, how to run it, and what to send back. Everything else in
  this folder (file tools, permissions, MCP servers, a web UI) hangs off
  this one loop.

WHAT YOU'LL LEARN:
  1. The four-step loop above, written out with nothing hidden
  2. What a "tool" is to a model: a name, a description, and a JSON
     schema for its arguments -- the description is the whole interface
  3. Why the loop needs a turn limit (a model can loop forever)
  4. How tool results re-enter the conversation so the model can use them
  5. That swapping the mock model for a real one changes nothing else

Concepts:
  - Tool: {name, description, parameters-schema, python callable}
  - Tool call: the model's request to run a tool -- {name, arguments}
  - Tool result: what your code sends back after running it
  - Turn: one round-trip to the model
  - Agentic loop: repeating until the model stops asking for tools

Flow:
     user: "how many words are in notes.txt?"
              |
              v
     +--------------------------+
     |  messages + tool specs   | ---------> MODEL
     +--------------------------+              |
              ^                                 v
              |                    reply.tool_calls = [read_file(...)]
              |                                 |
              |                                 v
              |                       YOUR CODE runs the tool
              |                                 |
              +----- append tool result --------+
              |
              |  (loop -- model now has the file contents)
              v
     MODEL replies with TEXT, no tool calls -> loop ends, answer returned

  Maps to:
    Claude Code's core loop; learn-langgraph lesson 07 (create_react_agent)
    is this same loop with LangGraph's state machine wrapped around it.

PREREQUISITES: None. Runs with no credentials (uses a mock model).

Run:  uv run python 01_agent_loop.py

EXPECTED OUTPUT:
  === Tools available to the model ===
    word_count(text) -- Count the words in a piece of text.

  === Turn 1 ===
    model -> TOOL CALL  word_count({'text': 'the quick brown fox jumps'})
    result <- {'words': 5}

  === Turn 2 ===
    model -> TEXT  "That text has 5 words."

  Loop ended after 2 turns.
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Callable


# ============================================================================
# STEP 1: What a "tool" is
# ============================================================================
# To a model, a tool is just three pieces of text plus a schema. The model
# never sees your Python function -- it only sees `name`, `description`,
# and `parameters`. That description IS the interface: a vague description
# is the single most common reason a model calls the wrong tool.

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict  # JSON Schema describing the arguments
    fn: Callable      # the actual Python function YOUR code runs


async def word_count(text: str) -> dict:
    """Count the words in a piece of text."""
    return {"words": len(text.split())}


TOOLS = {
    "word_count": Tool(
        name="word_count",
        description="Count the words in a piece of text.",
        parameters={
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text to count"}},
            "required": ["text"],
        },
        fn=word_count,
    )
}


# ============================================================================
# STEP 2: What the model returns
# ============================================================================
# Every provider (Anthropic, OpenAI, Azure) returns some version of this:
# either text, or a list of requested tool calls. The field names differ;
# the shape does not.

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class ModelReply:
    text: str | None = None
    tool_calls: list[ToolCall] | None = None


class MockModel:
    """A stand-in model so this lesson runs with zero credentials.

    Its "reasoning" is a hardcoded script: ask for word_count the first
    time, then answer using the result. A real model decides this itself,
    but the LOOP around it -- which is what this lesson teaches -- is
    byte-for-byte identical. Lesson 04 swaps in the real thing.
    """

    def __init__(self):
        self.turn = 0

    async def complete(self, messages: list[dict], tools: dict[str, Tool]) -> ModelReply:
        self.turn += 1
        if self.turn == 1:
            user_text = messages[-1]["content"]
            # A real model extracts this from the request; we fake it.
            target = "the quick brown fox jumps"
            return ModelReply(tool_calls=[
                ToolCall(id="call_1", name="word_count", arguments={"text": target})
            ])
        # Second turn: the tool result is now in `messages`, so answer from it.
        last_result = json.loads(messages[-1]["content"])
        return ModelReply(text=f"That text has {last_result['words']} words.")


# ============================================================================
# STEP 3: The loop -- this is the whole agent
# ============================================================================

async def agent_loop(model, tools: dict[str, Tool], user_message: str, max_turns: int = 6) -> str:
    messages: list[dict] = [{"role": "user", "content": user_message}]

    for turn in range(1, max_turns + 1):
        print(f"=== Turn {turn} ===")
        reply = await model.complete(messages, tools)

        # Case A: the model is done -- it replied with text, no tool calls.
        if not reply.tool_calls:
            print(f'    model -> TEXT  "{reply.text}"')
            print()
            print(f"  Loop ended after {turn} turns.")
            return reply.text or ""

        # Case B: the model wants tools run. YOUR code runs them -- the
        # model has no ability to execute anything on its own.
        for call in reply.tool_calls:
            print(f"    model -> TOOL CALL  {call.name}({call.arguments})")
            tool = tools.get(call.name)
            if tool is None:
                # Tell the model instead of crashing -- it can recover.
                result: Any = {"error": f"unknown tool: {call.name}"}
            else:
                result = await tool.fn(**call.arguments)
            print(f"    result <- {result}")

            # The result goes back into the conversation. Next turn the
            # model sees it and can use it. This is the whole mechanism
            # by which an agent "learns" anything about your machine.
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })
        print()

    # Turn limit: without this, a confused model can call tools forever.
    return "Stopped: hit the turn limit without a final answer."


# ============================================================================
# Demo
# ============================================================================

async def main():
    print("=== Tools available to the model ===")
    for tool in TOOLS.values():
        args = ", ".join(tool.parameters["properties"].keys())
        print(f"    {tool.name}({args}) -- {tool.description}")
    print()

    answer = await agent_loop(
        model=MockModel(),
        tools=TOOLS,
        user_message="how many words are in 'the quick brown fox jumps'?",
    )
    print(f"  Final answer: {answer}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # An "AI agent" is a while-loop with three rules:
    #   1. The model can only ASK for a tool; your code decides to run it.
    #      Every safety control you'll add (lesson 02's permission prompts,
    #      path sandboxing) lives in that gap between ask and run.
    #   2. Tool results must go back into the conversation, or the model
    #      re-asks for the same thing forever.
    #   3. Always cap the turns. A model that misreads a tool result can
    #      loop indefinitely, and each turn costs tokens.
    #
    # The model is stateless between calls -- `messages` is the entire
    # memory. That's why context management matters: the conversation is
    # the agent's only memory of what it has already done.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a second tool (`reverse_text`) and extend MockModel to call
    #    both in one turn -- note the loop already handles multiple calls.
    # 2. Make MockModel request an unknown tool name and watch the loop
    #    recover by reporting the error back instead of crashing.
    # 3. Set max_turns=1 and confirm you get the turn-limit message.
    # 4. Log each turn's `messages` length -- this is your context growing,
    #    and it's what eventually forces compaction in a long session.
