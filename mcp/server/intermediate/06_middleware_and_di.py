"""Middleware & dependency injection -- add behaviour WITHOUT editing the tool
====================================================================================

MIDDLEWARE wraps every request like an onion:

    request ──► A ──► B ──► tool ──► B ──► A ──► response      (A added first = outermost)

  - call_next(context) continues; not calling it stops the request
  - hooks: on_message -> on_request -> on_call_tool  (also on_list_tools, on_read_resource, ...)
  - DENY by raising ToolError -- never return None
  - hiding a tool from on_list_tools doesn't block calling it -- block both
  - built-ins: Logging, Timing, RateLimiting, ErrorHandling, ResponseCaching, ResponseLimiting

DEPENDENCY INJECTION fills a parameter at call time -- hidden from the client schema:

    Depends(fn)          your function's result (deps can use deps; computed ONCE per request)
    CallArgument()       another argument of the same call
    CurrentContext()  CurrentFastMCP()  CurrentHeaders()  CurrentRequest()
    CurrentAccessToken()  TokenClaim("sub")      (need auth)

Level: INTERMEDIATE
Run:  uv run python intermediate/06_middleware_and_di.py      (from mcp/server)
"""

import asyncio

from fastmcp import Client, FastMCP
from fastmcp.dependencies import CallArgument, CurrentFastMCP, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware
from fastmcp.server.middleware.timing import TimingMiddleware

mcp = FastMCP("GreetingService")


# ================================================================ middleware
class Trace(Middleware):
    """Shows the order: first added is outermost."""
    def __init__(self, label: str):
        self.label = label

    async def on_call_tool(self, context, call_next):
        print(f"    {self.label} in  -> {context.message.name}")
        result = await call_next(context)
        print(f"    {self.label} out")
        return result


class Guard(Middleware):
    """Deny, rewrite the request, enrich the result, and stamp state."""
    async def on_call_tool(self, context, call_next):
        if context.message.name == "delete_all":
            raise ToolError("admin only")                                 # DENY
        if context.message.name == "greet":
            context.message.arguments["name"] = context.message.arguments["name"].strip().title()  # REWRITE
        await context.fastmcp_context.set_state("caller", "ada@example.com")                       # STATE
        result = await call_next(context)
        if result.structured_content:
            result.structured_content["checked"] = True                   # ENRICH
        return result


mcp.add_middleware(Trace("A"))
mcp.add_middleware(Trace("B"))
mcp.add_middleware(Guard())
mcp.add_middleware(TimingMiddleware())       # a built-in


# ======================================================================= DI
def get_config() -> dict:
    print("    [dep] get_config runs once")
    return {"template": "Hello, {name}!", "language": "en"}


def get_template(config: dict = Depends(get_config)) -> str:    # a dep that uses a dep
    return config["template"]


def get_plan(name: str = CallArgument()) -> str:               # reads the call's `name`
    return "pro" if name.startswith("A") else "free"


@mcp.tool
def greet(
    name: str,
    template: str = Depends(get_template),   # none of these three
    plan: str = Depends(get_plan),           # appear in the schema
    server: FastMCP = CurrentFastMCP(),
) -> dict:
    return {"greeting": template.format(name=name), "plan": plan, "server": server.name}


@mcp.tool
def delete_all() -> str:
    return "deleted"


async def main():
    async with Client(mcp) as c:
        schema = next(t for t in await c.list_tools() if t.name == "greet").input_schema
        print("greet schema args ->", list(schema["properties"]), "(deps hidden)")
        print("call greet('  ada  '):")
        print("  ->", (await c.call_tool("greet", {"name": "  ada  "})).structured_content)
        r = await c.call_tool("delete_all", raise_on_error=False)
        print("delete_all ->", r.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
