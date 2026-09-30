"""The one server every client lesson talks to.

Not a lesson itself -- this is the "greeting service" from
learn-fastmcp-server, extended with one tool per client feature (progress,
logging, elicitation, sampling, roots, background tasks) so every lesson in
this folder has something real to call. Read learn-fastmcp-server first if
you want to know how any of *this* file works; this folder is about the
client calling it.

Runs three ways, all used by lesson 02:
    uv run python target_server.py            in-process demo (this file's own main)
    uv run python target_server.py --stdio    a real stdio server (subprocess)
    uv run python target_server.py --http PORT  a real HTTP server
"""

import asyncio
import sys

from fastmcp import Context, FastMCP
from fastmcp_tasks import TasksExtension
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from mcp.types import (
    CreateMessageRequest,
    CreateMessageRequestParams,
    CreateMessageResult,
    ElicitRequest,
    ElicitRequestFormParams,
    InputRequiredResult,
    ListRootsRequest,
    ListRootsResult,
    SamplingMessage,
    TextContent,
    ToolListChangedNotification,
)

mcp = FastMCP(
    name="GreetingService",
    instructions="Greets people by name, and demonstrates every FastMCP client feature.",
)
mcp.add_extension(TasksExtension())  # required for @mcp.tool(task=True) below

HELLO = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}


# ------------------------------------------------------------- the basics
@mcp.tool
def greet(name: str) -> str:
    """Greets someone by name."""
    return f"Hello, {name}!"


@mcp.tool
def farewell(name: str) -> str:
    """Says goodbye to someone by name."""
    return f"Goodbye, {name}!"


@mcp.resource("data://greeting")
def greeting_config() -> dict:
    """A fixed piece of data at a fixed URI."""
    return {"template": "Hello, {name}!", "language": "en"}


@mcp.resource("greet://{name}")
def greeting_for(name: str) -> dict:
    """Same idea, but the URI has a placeholder."""
    return {"name": name, "greeting": f"Hello, {name}!"}


@mcp.prompt
def ask_greeting(name: str) -> str:
    """Asks the LLM to write a greeting for someone."""
    return f"Write a warm, one-line greeting for someone called {name}."


# ------------------------------------------------- progress + logging (09, 10)
@mcp.tool
async def greet_slowly(names: list[str], ctx: Context) -> dict:
    """Greets a list of people, reporting progress and logging as it goes."""
    await ctx.info(f"Greeting {len(names)} people")
    greetings = []
    for i, name in enumerate(names):
        await ctx.report_progress(progress=i, total=len(names), message=f"greeting {name}")
        await asyncio.sleep(0.05)
        greetings.append(f"Hello, {name}!")
    await ctx.report_progress(progress=len(names), total=len(names))
    return {"greeted": len(greetings), "greetings": greetings}


# ------------------------------------------------------- elicitation (07, 08)
@mcp.tool
async def greet_with_approval(name: str, ctx: Context) -> str | InputRequiredResult:
    """Drafts a greeting, then asks the client to approve it before returning."""
    if ctx.input_responses is None:
        params = ElicitRequestFormParams(
            message=f"Approve this greeting for {name}?",
            requested_schema={
                "type": "object",
                "properties": {"approved": {"type": "boolean"}},
                "required": ["approved"],
            },
        )
        return InputRequiredResult(
            result_type="input_required",
            input_requests={"approve": ElicitRequest(method="elicitation/create", params=params)},
        )
    answer = ctx.input_responses["approve"]
    if answer.action != "accept" or not answer.content.get("approved"):
        return "Greeting was not approved."
    return f"Hello, {name}!"


# ----------------------------------------------------------- sampling (06)
@mcp.tool
async def greet_creatively(name: str, ctx: Context) -> str | InputRequiredResult:
    """Asks the CALLING CLIENT's model to write a creative greeting."""
    if ctx.input_responses is None:
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
                                    type="text", text=f"Write one imaginative greeting for {name}."
                                ),
                            )
                        ],
                        max_tokens=100,
                    ),
                )
            },
        )
    answer = ctx.input_responses["greeting"]
    if isinstance(answer, CreateMessageResult) and isinstance(answer.content, TextContent):
        return answer.content.text
    return "The client returned no completion."


# --------------------------------------------------------------- roots (11)
@mcp.tool
async def list_client_roots(ctx: Context) -> list[str] | InputRequiredResult:
    """Asks the client which filesystem roots it has made available.

    Same guard pattern as elicitation/sampling (see greet_with_approval and
    greet_creatively above): return the request as a RESULT instead of
    pushing it down the connection, so this works on the modern protocol too.
    """
    if ctx.input_responses is None:
        return InputRequiredResult(
            result_type="input_required",
            input_requests={"roots": ListRootsRequest(method="roots/list")},
        )
    answer = ctx.input_responses["roots"]
    if isinstance(answer, ListRootsResult):
        return [str(r.uri) for r in answer.roots]
    return []


# ---------------------------------------------------------- background tasks (08)
@mcp.tool(task=True)
async def greet_in_background(names: list[str]) -> str:
    """A slow job the client can run as a background task instead of waiting."""
    await asyncio.sleep(0.3)
    return f"Greeted {len(names)} people in the background: {', '.join(names)}"


# ------------------------------------------------------- notifications (12)
@mcp.tool
async def add_translate_tool(ctx: Context) -> str:
    """Registers a new tool at runtime and tells any listening client."""

    @mcp.tool
    def translate(text: str, language: str) -> str:
        """Translates text into another language (simulated)."""
        return f"[{language}] {text}"

    await ctx.send_notification(
        ToolListChangedNotification(method="notifications/tools/list_changed")
    )
    return "translate tool added"


# used by lesson 02 to know when the HTTP subprocess is ready
@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


# ----------------------------------------------------------------- __main__
if __name__ == "__main__":
    if "--stdio" in sys.argv:
        mcp.run(show_banner=False)
    elif "--http" in sys.argv:
        port = int(sys.argv[sys.argv.index("--http") + 1])
        mcp.run(transport="http", host="127.0.0.1", port=port, show_banner=False)
    else:
        print("This file is the target server for every lesson in this folder.")
        print("Run a lesson instead, e.g.:  uv run python 01_client_basics.py")
