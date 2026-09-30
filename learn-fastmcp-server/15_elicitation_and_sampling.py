"""Lesson 15 -- Elicitation and sampling: asking the client for something
=========================================================================

Lesson 09 hit a wall: ctx.elicit() raised an error, and ctx.sample() didn't
even exist. This lesson explains why, and shows the replacement. The tool
still just greets someone -- it only has to ask WHO and in WHICH LANGUAGE
first.

WHY IT CHANGED: elicit() and sample() used to pause the tool mid-run, ask
the client a question over the open connection, and resume once answered.
The modern MCP protocol doesn't allow the server to push a question like
that anymore (partly so servers can be stateless and load-balanced, where
"the same worker is still there to resume" isn't a safe assumption).

THE REPLACEMENT: the GUARD PATTERN. Instead of pausing, the tool just
RETURNS a question, and the client calls it again with the answer:

    round 1   nothing answered yet     -> return a question
    round 2   got an answer            -> read it, maybe ask another question
    round 3   ...                      -> return the real result

Each round is a complete, independent request -- the tool remembers nothing
between rounds by itself. To carry a value (like a name) from round 1 to
round 3, stash it in ctx.request_state, a string FastMCP seals so the
client can't read or tamper with it.

Run:  uv run python 15_elicitation_and_sampling.py
"""

import asyncio

from fastmcp import Client, Context, FastMCP
from fastmcp.client.elicitation import ElicitResult
from fastmcp.tools import InputRequiredToolResult
from mcp.types import (
    CreateMessageRequest,
    CreateMessageRequestParams,
    CreateMessageResult,
    ElicitRequest,
    ElicitRequestFormParams,
    InputRequiredResult,
    SamplingMessage,
    TextContent,
)

mcp = FastMCP("GreetingService")

HELLO = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}


# --------------------------------------------------------------- the helper
def ask(key: str, message: str, field: str, request_state: str | None = None) -> InputRequiredResult:
    """Build an InputRequiredResult that elicits one text field.

    `key` matters: the answer comes back under the SAME key in
    ctx.input_responses, which is how one round can ask several things at once.
    """
    params = ElicitRequestFormParams(
        message=message,
        requested_schema={
            "type": "object",
            "properties": {field: {"type": "string"}},
            "required": [field],
        },
    )
    return InputRequiredResult(
        result_type="input_required",
        input_requests={key: ElicitRequest(method="elicitation/create", params=params)},
        request_state=request_state,
    )


# ------------------------------------------------- 1. a three-round greeting
@mcp.tool
async def greet_interactively(ctx: Context) -> str | InputRequiredResult:
    """Greet someone, asking who and in which language across three rounds."""
    responses = ctx.input_responses

    if responses is None:                       # round 1: nothing asked yet
        return ask("name", "Who would you like to greet?", "name")

    if "name" in responses:                     # round 2: got the name
        name = responses["name"].content["name"]
        return ask(
            "language",
            f"Which language should I greet {name} in?",
            "language",
            request_state=f"name={name}",          # carry it forward, sealed
        )

    # round 3: got the language; recover the name from the sealed state
    name = ctx.request_state.split("=", 1)[1]
    language = responses["language"].content["language"]
    return f"{HELLO.get(language, 'Hello')}, {name}!"


# ------------------------------------------- 2. declines are normal answers
@mcp.tool
async def confirm_delete_greeting(ctx: Context) -> str | InputRequiredResult:
    """A decline is an ANSWER, not an error -- check action before content."""
    responses = ctx.input_responses
    if responses is None:
        return ask("ok", "Type DELETE to remove every saved greeting:", "ok")

    answer = responses["ok"]
    if answer.action != "accept":               # declined or cancelled
        return f"Cancelled ({answer.action}) -- no greetings were deleted."
    return f"Proceeding with {answer.content['ok']}"


# -------------------------------------- 3. prompts and resources too
# InputRequiredResult is a RESULT TYPE, not a tools feature. Any request can
# resolve to one, and the client drives the loop the same way.
ask_for_language = InputRequiredResult(
    result_type="input_required",
    input_requests={
        "language": ElicitRequest(
            method="elicitation/create",
            params=ElicitRequestFormParams(
                message="Which language should the greeting use?",
                requested_schema={
                    "type": "object",
                    "properties": {"language": {"type": "string"}},
                    "required": ["language"],
                },
            ),
        )
    },
)


@mcp.prompt
async def ask_greeting(ctx: Context) -> str | InputRequiredResult:
    """A PROMPT that asks a question before it renders."""
    responses = ctx.input_responses
    if responses is None:
        return ask_for_language
    language = responses["language"].content["language"]
    return f"Write a greeting in {language}."


@mcp.resource("greeting://template")
async def greeting_template(ctx: Context) -> str | InputRequiredResult:
    """A RESOURCE that asks a question before it resolves."""
    responses = ctx.input_responses
    if responses is None:
        return ask_for_language
    language = responses["language"].content["language"]
    return f"{HELLO.get(language, 'Hello')}, {{name}}!"


# ------------------------------------------------- 4. sampling, the new way
# Sampling means borrowing the CALLER's model: their provider, their
# credentials, their bill. Slot a CreateMessageRequest into input_requests
# the exact same way you would an ElicitRequest.
#
# Note: ctx.sample() itself was removed in FastMCP 4 -- use this pattern.
@mcp.tool
async def greet_creatively(name: str, ctx: Context) -> str | InputRequiredResult:
    """Ask the CALLER's model to invent a greeting, then return it."""
    responses = ctx.input_responses
    if responses is None:
        return InputRequiredResult(
            result_type="input_required",
            input_requests={
                "greeting": CreateMessageRequest(
                    method="sampling/createMessage",
                    params=CreateMessageRequestParams(
                        messages=[
                            SamplingMessage(
                                role="user",
                                content=TextContent(
                                    type="text",
                                    text=f"Write one imaginative greeting for {name}.",
                                ),
                            )
                        ],
                        max_tokens=100,
                    ),
                )
            },
        )

    answer = responses["greeting"]
    if isinstance(answer, CreateMessageResult) and isinstance(answer.content, TextContent):
        return answer.content.text
    return "The client returned no completion."


# For most work, DON'T ask the caller for a model -- just call an LLM
# directly from the server. It's plain application code: works with every
# client, no round trip, and you choose the model and see the token usage.
#
#   llm = anthropic.AsyncAnthropic()          # module scope: reuse connections
#
#   @mcp.tool
#   async def greet_poetically(name: str) -> str:
#       response = await llm.messages.create(
#           model="claude-sonnet-4-5", max_tokens=512,
#           messages=[{"role": "user", "content": f"Write one poetic greeting for {name}."}],
#       )
#       return response.content[0].text
#
# Ask the caller's model only when using THEIR specific model is the goal.


async def elicitation_handler(message, response_type, params, ctx):
    """The client side. fastmcp.Client drives every round by itself."""
    print(f"    [client] {message}")
    if "Who" in message:
        return ElicitResult(action="accept", content=response_type(name="Ada"))
    if "Which language" in message or "language should the greeting" in message:
        return ElicitResult(action="accept", content=response_type(language="fr"))
    if "DELETE" in message:
        return ElicitResult(action="decline")            # user says no
    return ElicitResult(action="cancel")


async def sampling_handler(messages, params, ctx):
    """Stands in for the caller's LLM."""
    print(f"    [client LLM] asked: {messages[0].content.text}")
    return "Greetings and salutations, Ada!"


async def main():
    # mode="auto" negotiates the modern protocol. input_required_max_rounds
    # (default 10) stops a broken guard from looping forever.
    async with Client(
        mcp,
        mode="auto",
        elicitation_handler=elicitation_handler,
        sampling_handler=sampling_handler,
        input_required_max_rounds=10,
    ) as client:
        print("greet_interactively (3 rounds, client drives the loop):")
        r = await client.call_tool("greet_interactively", {})
        print("  ->", r.data)

        print("\nconfirm_delete_greeting (client declines):")
        r = await client.call_tool("confirm_delete_greeting", {})
        print("  ->", r.data)

        print("\nthe same pattern on a prompt:")
        p = await client.get_prompt("ask_greeting", {})
        print("  ->", p.messages[0].content.text)

        print("\nthe same pattern on a resource:")
        res = await client.read_resource("greeting://template")
        print("  ->", res[0].text)

        print("\nsampling -- borrowing the caller's model:")
        r = await client.call_tool("greet_creatively", {"name": "Ada"})
        print("  ->", r.data)

    # ctx.sample is gone, not merely unavailable
    print("\nhasattr(Context, 'sample'):", hasattr(Context, "sample"))
    try:
        FastMCP("X", sampling_handler=sampling_handler)
    except TypeError as e:
        print("FastMCP(sampling_handler=...) ->", str(e)[:88])

    # An asking round returns InputRequiredToolResult (a ToolResult subclass);
    # the final round returns a plain ToolResult. Middleware sees every round,
    # and an ask is a legitimate result -- not an error to be handled.
    print("\nInputRequiredToolResult is a ToolResult subclass:",
          InputRequiredToolResult.__mro__[1].__name__)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Make the elicitation_handler return action="cancel" for "Who". Note the
#    tool still completes -- a cancel is an answer it can act on.
# 2. Ask for the name AND language in ONE round (two keys in one
#    input_requests map) and read both from ctx.input_responses.
# 3. Drop request_state from round 2 of greet_interactively. Round 3 can no
#    longer recover the name -- the tool keeps NOTHING between rounds.
# 4. Set input_required_max_rounds=1 and watch the loop get cut off.
# 5. Multi-replica deployments need a shared sealing key, or round 3 on
#    another worker cannot verify the state:
#       FastMCP("S", request_state_security=RequestStateSecurity(
#           keys=[os.environ["REQUEST_STATE_KEY"].encode()]))
#    Keys need >=32 bytes of randomness; `keys` is a rotation ring where
#    keys[0] seals and every key can unseal.
# 6. On a handshake-era connection, ctx.elicit() is the right call and
#    accepts response_type=str / int / bool / ["en","fr"] / [["en","fr"]]
#    (multi-select) / a dataclass / a Literal / an Enum, returning
#    AcceptedElicitation | DeclinedElicitation | CancelledElicitation.
