"""Server requests -- the SERVER asks the CLIENT for something
====================================================================

    ELICITATION  ask the caller's USER a question
    SAMPLING     run text through the caller's LLM (their model, their bill)

The old way (ctx.elicit / ctx.sample) PAUSED the tool -- the modern protocol
forbids that. The new way is the GUARD PATTERN: return the question, get re-called.

    call 1: input_responses is None    -> return InputRequiredResult(question)
    call 2: input_responses["key"]     -> the answer -> finish (or ask again)

  - the answer comes back under the SAME key you asked with
  - the tool remembers nothing between calls -> carry values in request_state
    (sealed by FastMCP; multi-replica? share RequestStateSecurity(keys=[...]))
  - "decline" / "cancel" are answers, not errors -- check .action
  - works on prompts and resources too
  - usually simpler: call an LLM directly from the server; sample only when you
    need the CALLER's model
  - learn-mcp lesson 06's continuation_token is a different, incompatible scheme

Client side: ../../client/intermediate/05_server_requests.py

Level: INTERMEDIATE
Run:  uv run python intermediate/05_server_requests.py      (from mcp/server)
"""

import asyncio

from fastmcp import Client, Context, FastMCP
from fastmcp.client.elicitation import ElicitResult
from mcp.types import (
    CreateMessageRequest, CreateMessageRequestParams, ElicitRequest, ElicitRequestFormParams,
    InputRequiredResult, SamplingMessage, TextContent,
)

mcp = FastMCP("GreetingService")


def ask(key: str, question: str, state: str | None = None) -> InputRequiredResult:
    """A question asking for one text field named `key`."""
    schema = {"type": "object", "properties": {key: {"type": "string"}}, "required": [key]}
    params = ElicitRequestFormParams(message=question, requested_schema=schema)
    return InputRequiredResult(result_type="input_required", request_state=state,
                               input_requests={key: ElicitRequest(method="elicitation/create", params=params)})


# ------------------------------------------------ 1. elicitation, 3 rounds
@mcp.tool
async def greet_interactively(ctx: Context) -> str | InputRequiredResult:
    answers = ctx.input_responses
    if answers is None:
        return ask("name", "Who would you like to greet?")
    if "name" in answers:
        name = answers["name"].content["name"]
        return ask("language", f"Which language for {name}?", state=name)   # carry the name
    hello = {"fr": "Bonjour", "de": "Hallo"}.get(answers["language"].content["language"], "Hello")
    return f"{hello}, {ctx.request_state}!"


# --------------------------------------------- 2. a decline is an answer
@mcp.tool
async def confirm_delete(ctx: Context) -> str | InputRequiredResult:
    if ctx.input_responses is None:
        return ask("ok", "Type DELETE to remove every greeting:")
    answer = ctx.input_responses["ok"]
    return "Deleted." if answer.action == "accept" else f"Cancelled ({answer.action})."


# ------------------------------------------ 3. a prompt can ask too
@mcp.prompt
async def ask_greeting(ctx: Context) -> str | InputRequiredResult:
    if ctx.input_responses is None:
        return ask("language", "Which language?")
    return f"Write a greeting in {ctx.input_responses['language'].content['language']}."


# ------------------------------------------------------------ 4. sampling
@mcp.tool
async def greet_creatively(name: str, ctx: Context) -> str | InputRequiredResult:
    if ctx.input_responses is None:
        msg = SamplingMessage(role="user", content=TextContent(type="text", text=f"Greet {name} creatively."))
        req = CreateMessageRequest(method="sampling/createMessage",
                                   params=CreateMessageRequestParams(messages=[msg], max_tokens=100))
        return InputRequiredResult(result_type="input_required", input_requests={"llm": req})
    return ctx.input_responses["llm"].content.text


# -------------------------------------------------- the client, for the demo
async def on_question(message, response_type, params, ctx):
    print(f"    [client asked] {message}")
    if "Who" in message:
        return ElicitResult(action="accept", content=response_type(name="Ada"))
    if "language" in message:
        return ElicitResult(action="accept", content=response_type(language="fr"))
    return ElicitResult(action="decline")


async def on_sample(messages, params, ctx):
    return "Greetings and salutations, Ada!"


async def main():
    async with Client(mcp, elicitation_handler=on_question, sampling_handler=on_sample) as c:
        print("3 rounds  ->", (await c.call_tool("greet_interactively", {})).data)
        print("decline   ->", (await c.call_tool("confirm_delete", {})).data)
        print("prompt    ->", (await c.get_prompt("ask_greeting", {})).messages[0].content.text)
        print("sampling  ->", (await c.call_tool("greet_creatively", {"name": "Ada"})).data)


if __name__ == "__main__":
    asyncio.run(main())
