"""Lesson 18 -- Middleware and dependency injection
==================================================

Two ways to add cross-cutting behaviour to greet() without editing greet().

   MIDDLEWARE -- wraps every request
   ──────────────────────────────────
   Request -> A -> B -> handler -> B -> A -> Response
   call_next(context) continues the chain; skipping it stops everything.
   Insertion order = nesting order: whichever is added FIRST is OUTERMOST.
   A tool call fires three hook levels in order: on_message, then
   on_request, then a specific hook like on_call_tool.

   DEPENDENCY INJECTION -- fills a function's parameters for you
   ────────────────────────────────────────────────────────────
   Give a parameter a special default and FastMCP resolves it at call time.
   These parameters are hidden from the client's schema entirely.

     CurrentContext()      the running Context
     CurrentFastMCP()      the server instance
     CurrentHeaders()      the HTTP headers (empty dict off HTTP)
     Depends(fn)           run any function of your own and inject its result
     CallArgument()        read an argument of the same call

   If two parameters depend on the same thing, it's only computed once per
   request -- the result is cached and shared.

Run:  uv run python 18_middleware_and_di.py
"""

import asyncio
import time

from fastmcp import Client, Context, FastMCP
from fastmcp.dependencies import CallArgument, CurrentFastMCP, Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware


# ======================================================== 1. the hook levels
class TraceMiddleware(Middleware):
    """One tool call fires on_message, then on_request, then on_call_tool."""

    def __init__(self, label: str, sink: list[str]):
        self.label, self.sink = label, sink

    async def on_message(self, context: MiddlewareContext, call_next):
        self.sink.append(f"{self.label} on_message   -> {context.method}")
        result = await call_next(context)
        self.sink.append(f"{self.label} on_message   <- {context.method}")
        return result

    async def on_request(self, context: MiddlewareContext, call_next):
        self.sink.append(f"{self.label} on_request   -> {context.method}")
        return await call_next(context)

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        # context.message carries .name and .arguments
        self.sink.append(f"{self.label} on_call_tool -> {context.message.name}")
        return await call_next(context)


async def demo_hooks_and_order():
    trace: list[str] = []
    mcp = FastMCP("GreetingService")

    @mcp.tool
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    mcp.add_middleware(TraceMiddleware("A", trace))   # added first -> outermost
    mcp.add_middleware(TraceMiddleware("B", trace))   # inner

    async with Client(mcp) as c:
        await c.call_tool("greet", {"name": "Ada"})

    print("hook order for one greet() call:")
    for line in trace:
        print("  ", line)
    print("  ^ A wraps B: first added is outermost, and unwinds last")


# ============================================ 2. deny, modify, filter, state
class GreetingGuard(Middleware):
    """Deny by RAISING -- never return a sentinel or silently skip call_next."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        if context.message.name == "delete_all_greetings":
            # ToolError for tools; ResourceError / PromptError / McpError elsewhere
            raise ToolError("Access denied: requires admin privileges")
        return await call_next(context)


class NameNormalizer(Middleware):
    """Mutate the request on the way IN."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        if context.message.name == "greet":
            raw = context.message.arguments.get("name", "")
            context.message.arguments["name"] = raw.strip().title()
        return await call_next(context)


class GreetingEnricher(Middleware):
    """Mutate the result on the way OUT."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        result = await call_next(context)
        if context.message.name == "greet" and result.structured_content:
            result.structured_content["processed_by"] = "enricher"
        return result


class PrivateToolFilter(Middleware):
    """Filtering a LIST is not blocking EXECUTION -- do both."""

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        tools = await call_next(context)
        return [t for t in tools if "private" not in t.tags]

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        if context.fastmcp_context:
            tool = await context.fastmcp_context.fastmcp.get_tool(context.message.name)
            if tool and "private" in tool.tags:
                raise ToolError("Tool not found")
        return await call_next(context)


class CallerMiddleware(Middleware):
    """Middleware writes state; the tool reads it (same request only)."""

    async def on_request(self, context: MiddlewareContext, call_next):
        ctx = context.fastmcp_context
        # Guard request_context: there is no session during initialize.
        if ctx and ctx.request_context:
            await ctx.set_state("caller", "ada@example.com")
        return await call_next(context)


async def demo_behaviours():
    mcp = FastMCP("GreetingService")

    @mcp.tool
    def greet(name: str) -> dict:
        """Greets someone by name."""
        return {"greeting": f"Hello, {name}!"}

    @mcp.tool
    def delete_all_greetings() -> str:
        """Admin-only."""
        return "deleted"

    @mcp.tool(tags={"private"})
    def greet_internal(name: str) -> str:
        """Should not be listed or callable."""
        return f"[internal] {name}"

    @mcp.tool
    async def greet_caller(ctx: Context) -> str:
        """Greets whoever the middleware identified."""
        return f"Hello, {await ctx.get_state('caller')}!"

    for mw in (GreetingGuard(), NameNormalizer(), GreetingEnricher(),
               PrivateToolFilter(), CallerMiddleware()):
        mcp.add_middleware(mw)

    async with Client(mcp) as c:
        print("\nlisted tools (private filtered):", sorted(t.name for t in await c.list_tools()))

        r = await c.call_tool("greet", {"name": "  ada  "})
        print("  request rewritten + response enriched ->", r.structured_content)

        r = await c.call_tool("delete_all_greetings", raise_on_error=False)
        print("  denied by raising      -> isError =", r.is_error, "|", r.content[0].text)

        r = await c.call_tool("greet_internal", {"name": "x"}, raise_on_error=False)
        print("  hidden AND blocked     -> isError =", r.is_error)

        print("  state from middleware  ->", (await c.call_tool("greet_caller")).data)


# ==================================================== 3. built-in middleware
async def demo_builtins():
    """Stack them outermost-first: errors, then limits, then timing, then logs."""
    mcp = FastMCP("GreetingService")

    @mcp.tool
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    mcp.add_middleware(RateLimitingMiddleware(max_requests_per_second=50.0, burst_capacity=20))
    mcp.add_middleware(TimingMiddleware())
    mcp.add_middleware(LoggingMiddleware(include_payloads=True, max_payload_length=200))

    async with Client(mcp) as c:
        print("\nbuilt-ins ->", (await c.call_tool("greet", {"name": "Ada"})).data)

    print(
        "  also available out of the box:\n"
        "    LoggingMiddleware, TimingMiddleware, ResponseCachingMiddleware,\n"
        "    RateLimitingMiddleware, ErrorHandlingMiddleware, ResponseLimitingMiddleware\n"
    )


# ============================================== 4. dependency injection
def get_greeting_config() -> dict:
    """A plain function -- sync or async, both fine."""
    print("    [dep] building greeting config")      # printed ONCE per request
    return {"template": "Hello, {name}!", "language": "en"}


def get_formatter(config: dict = Depends(get_greeting_config)) -> dict:
    """Dependencies can depend on dependencies."""
    return {"kind": "formatter", "template": config["template"]}


def get_translator(config: dict = Depends(get_greeting_config)) -> dict:
    """Shares the SAME config instance as get_formatter -- cached per request."""
    return {"kind": "translator", "language": config["language"]}


def get_recipient_record(name: str = CallArgument()) -> dict:
    """CallArgument() reads an argument of the call being served.

    Bare CallArgument() adopts the name of the parameter it is attached to;
    CallArgument("name") is explicit. optional=True yields None if absent.
    """
    return {"name": name, "plan": "pro"}


async def demo_di():
    mcp = FastMCP("GreetingService")

    @mcp.tool
    async def greet(
        name: str,
        # none of these three appear in the client-facing schema
        formatter: dict = Depends(get_formatter),
        translator: dict = Depends(get_translator),
        server: FastMCP = CurrentFastMCP(),
    ) -> dict:
        """Greets someone by name."""
        return {
            "greeting": formatter["template"].format(name=name),
            "language": translator["language"],
            "server": server.name,
        }

    @mcp.tool
    async def greet_record(name: str, record: dict = Depends(get_recipient_record)) -> str:
        """A dependency that reads the call's own `name` argument."""
        return f"Hello, {record['name']}! (plan: {record['plan']})"

    async with Client(mcp) as c:
        tools = {t.name: t for t in await c.list_tools()}
        print("greet schema args:", list(tools["greet"].input_schema["properties"]),
              "  <- dependencies hidden")

        print("calling greet('Ada'):")
        r = await c.call_tool("greet", {"name": "Ada"})
        print("  ->", r.data)
        print("  ^ '[dep] building greeting config' printed ONCE, even though")
        print("    both get_formatter and get_translator depend on it")

        print("\ngreet_record('Ada') ->", (await c.call_tool("greet_record", {"name": "Ada"})).data)

    print(
        "\n  other built-in dependencies:\n"
        "    CurrentRequest()      the raw Starlette Request (HTTP only)\n"
        "    CurrentAccessToken()  raises if unauthenticated; get_access_token()\n"
        "                          returns None instead\n"
        "    TokenClaim('sub')     read one claim from the auth token\n"
        "  A dependency can be an @asynccontextmanager, so teardown runs after\n"
        "  the call -- even on errors. Clients cannot override a dependency by\n"
        "  sending an argument with the same name; it's stripped first.\n"
    )


async def main():
    await demo_hooks_and_order()
    await demo_behaviours()
    await demo_builtins()
    await demo_di()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Swap the order of the two TraceMiddleware instances. B becomes outermost.
# 2. In GreetingGuard, `return None` instead of raising. The client gets a
#    confusing empty result rather than an error -- raise, always.
# 3. Add on_initialize to TraceMiddleware and read
#    context.message.params.client_info.name. Rejecting AFTER call_next only
#    logs -- the client still receives success.
# 4. Override __call__ on a Middleware to bypass hook dispatch entirely.
# 5. Make get_greeting_config an @asynccontextmanager and print on teardown.
# 6. Point two Depends() at the same factory with DIFFERENT bindings
#    (Depends(fn, x=CallArgument("a")) vs x=CallArgument("b")) -- they no
#    longer share a cached result.
