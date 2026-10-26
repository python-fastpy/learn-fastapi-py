"""The greet server -- the ONE server every client lesson talks to
=======================================================================

Not a lesson itself (building servers is ../server). It has one thing per
client feature, so every lesson has something real to call:

    greet, resource, template, prompt     00, 03   the basics
    greet_slowly, add_translate_tool      04       progress, logging, notifications
    greet_creatively, greet_with_approval 05       sampling, elicitation, roots
      list_client_roots
    greet_in_background                   06       background tasks
    /health                               02       plain HTTP route

Run:  uv run python greet_server.py          stdio: prints NOTHING and waits on stdin
      uv run python greet_server.py --http   http:  POST /mcp  +  GET /health on :8765
"""

import asyncio
import sys

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from fastmcp_tasks import TasksExtension
from mcp.types import (
    CreateMessageRequest, CreateMessageRequestParams, CreateMessageResult, ElicitRequest,
    ElicitRequestFormParams, InputRequiredResult, ListRootsRequest, ListRootsResult,
    SamplingMessage, TextContent, ToolListChangedNotification,
)
from starlette.responses import JSONResponse

# `instructions` is what client.instructions returns after the handshake (00).
mcp = FastMCP("greetings", instructions="Greets people by name.")
mcp.add_extension(TasksExtension())        # needed for @mcp.tool(task=True) below


# --------------------------------------------------------------- basics
@mcp.tool
def greet(name: str) -> dict:
    """Greet someone by name."""
    if not name.strip():
        # ToolError -> the client gets is_error=True with this exact message
        # (or a raised ToolError, unless it passed raise_on_error=False).
        raise ToolError("name cannot be empty")
    result = {"greeting": f"Hello, {name}!"}
    # Headers exist only over HTTP. Under stdio / in-memory this dict is
    # empty, so the same tool works on every transport (see 02 tenant demo).
    tenant = get_http_headers().get("x-tenant-id")
    if tenant:
        result["tenant"] = tenant
    return result


# A FIXED resource: one URI -> client.list_resources() / read_resource("data://greeting")
@mcp.resource("data://greeting", mime_type="application/json")
def greeting_config() -> dict:
    return {"template": "Hello, {name}!"}


# A TEMPLATE: {name} is filled in by the client -> read_resource("greet://Ada")
@mcp.resource("greet://{name}")
def greeting_for(name: str) -> str:
    return f"Hello, {name}!"


# A prompt returns MESSAGES for an LLM -> client.get_prompt("ask_greeting", {...})
@mcp.prompt
def ask_greeting(name: str) -> str:
    """Asks the LLM to write a greeting."""
    return f"Write a warm, one-line greeting for {name}."


# ----------------------------------------- progress, logging, notifications
@mcp.tool
async def greet_slowly(names: list[str], ctx: Context) -> list[str]:
    """Greets people one by one, logging and reporting progress."""
    await ctx.info(f"Greeting {len(names)} people")          # -> client's log_handler
    for i, name in enumerate(names):
        # -> client's progress_handler(progress, total, message)
        await ctx.report_progress(progress=i, total=len(names), message=f"greeting {name}")
        await asyncio.sleep(0.05)                            # pretend this is slow work
    await ctx.report_progress(progress=len(names), total=len(names))
    return [f"Hello, {n}!" for n in names]


@mcp.tool
async def add_translate_tool(ctx: Context) -> str:
    """Adds a tool at runtime and tells listening clients the list changed."""
    @mcp.tool                                    # registering a NEW tool while running
    def translate(text: str, language: str) -> str:
        return f"[{language}] {text}"

    # Fire-and-forget "your cached tool list is stale" -> client's message_handler
    # (on_tool_list_changed). Calling this twice warns "already exists" -- harmless.
    await ctx.send_notification(ToolListChangedNotification(method="notifications/tools/list_changed"))
    return "translate tool added"


# ------------------------------------ the server asks the CLIENT for something
# Pattern for all three -- the tool runs TWICE:
#
#   call 1: ctx.input_responses is None  -> RETURN the question (InputRequiredResult)
#           the client runs its handler (sampling_handler / elicitation_handler / roots)
#   call 2: ctx.input_responses["key"]   -> the client's answer; finish the job
#
# The "key" you choose in input_requests={...} is how you find the answer again.
# The client does the re-call for you -- your client code is just one call_tool().
@mcp.tool
async def greet_creatively(name: str, ctx: Context) -> str | InputRequiredResult:
    """Sampling: asks the CLIENT's LLM to write the greeting."""
    if ctx.input_responses is None:
        # call 1: "please run this prompt through your LLM"
        msg = SamplingMessage(role="user", content=TextContent(type="text", text=f"Greet {name} creatively."))
        return InputRequiredResult(result_type="input_required", input_requests={
            "llm": CreateMessageRequest(method="sampling/createMessage",
                                        params=CreateMessageRequestParams(messages=[msg], max_tokens=100)),
        })
    # call 2: the client's sampling_handler returned this completion
    answer = ctx.input_responses["llm"]
    return answer.content.text if isinstance(answer, CreateMessageResult) else "no completion"


@mcp.tool
async def greet_with_approval(name: str, ctx: Context) -> str | InputRequiredResult:
    """Elicitation: asks the USER to approve before greeting."""
    if ctx.input_responses is None:
        # call 1: a question + the SHAPE of the answer (JSON Schema). The client
        # turns this schema into `response_type` for its elicitation_handler.
        params = ElicitRequestFormParams(
            message=f"Approve this greeting for {name}?",
            requested_schema={"type": "object", "properties": {"approved": {"type": "boolean"}},
                              "required": ["approved"]},
        )
        return InputRequiredResult(result_type="input_required", input_requests={
            "approve": ElicitRequest(method="elicitation/create", params=params),
        })
    # call 2: action is "accept" | "decline" | "cancel"; content holds the fields
    answer = ctx.input_responses["approve"]
    if answer.action != "accept" or not answer.content.get("approved"):
        return "Greeting was not approved."
    return f"Hello, {name}!"


@mcp.tool
async def list_client_roots(ctx: Context) -> list[str] | InputRequiredResult:
    """Roots: asks which folders the client allows this server to use."""
    if ctx.input_responses is None:
        # call 1: "list your roots" -- no params needed
        return InputRequiredResult(result_type="input_required",
                                   input_requests={"roots": ListRootsRequest(method="roots/list")})
    # call 2: whatever the client passed as roots=[...] or its roots callback returned
    answer = ctx.input_responses["roots"]
    return [str(r.uri) for r in answer.roots] if isinstance(answer, ListRootsResult) else []


# -------------------------------------------------------- background task
# task=True lets a client start this, get a task id back immediately, and poll
# (call_tool_task in 06). A plain call_tool() still works -- the client polls for you.
@mcp.tool(task=True)
async def greet_in_background(names: list[str]) -> str:
    """A slow job the client can run in the background instead of waiting."""
    await asyncio.sleep(0.3)                     # pretend this takes minutes
    return f"Greeted {len(names)} people: {', '.join(names)}"


# ----------------------------------------------------------- HTTP-only route
# A plain REST endpoint next to /mcp -- load balancers ping it; 02 waits on it
# to know the server is up. Doesn't exist under stdio (no URLs there).
@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "healthy"})


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run(
            transport="http", host="127.0.0.1", port=8765,
            json_response=True,     # reply with plain JSON, not an SSE stream
            stateless_http=True,    # no session between requests -> any container can answer
            show_banner=False,
        )
    else:
        # stdout IS the protocol channel -- the server must stay silent.
        mcp.run(show_banner=False)
