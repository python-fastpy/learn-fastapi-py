"""Lesson 10 -- Transforms: Namespace, tool transformation, custom
==================================================================

A transform sits between a provider and the client and rewrites components
on the way out -- without touching your functions. That's what makes it the
right tool for fixing up servers you do NOT own (mounted, proxied, generated).

Everything below reshapes one greet function.

    Provider -> [Transform A] -> [Transform B] -> Client
                 added first       added second
                 (innermost)        (outermost)

Every transform can implement two kinds of hooks (up to eight total --
list_tools/get_tool, and the same pair for resources, templates, prompts):
    list_tools(tools)           pure function: takes a list, returns a list
    get_tool(name, call_next)   for one lookup by name

WHAT NAMESPACE DOES (prefixes every name with "api")
    tool      greet             -> api_greet
    resource  data://greeting   -> data://api/greeting

Run:  uv run python 10_transforms_basics.py
"""

import asyncio
import uuid
from collections.abc import Sequence

from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.providers import FastMCPProvider
from fastmcp.server.transforms import GetToolNext, Namespace, ToolTransform, Transform
from fastmcp.tools import Tool, tool
from fastmcp.tools.tool_transform import ArgTransform, ToolTransformConfig, forward
from fastmcp.utilities.versions import VersionSpec


async def names(mcp: FastMCP) -> list[str]:
    async with Client(mcp) as c:
        return sorted(t.name for t in await c.list_tools())


# ============================================================== 1. Namespace
async def demo_namespace():
    english = FastMCP("English")
    french = FastMCP("French")

    @english.tool
    def greet(name: str) -> str:
        """Greets in English."""
        return f"Hello, {name}!"

    @english.resource("data://greeting")
    def config() -> str:
        return "Hello, {name}!"

    @french.tool
    def greet(name: str) -> str:  # noqa: F811 -- same name on purpose
        """Greets in French."""
        return f"Bonjour, {name}!"

    # Both servers export greet. Without namespaces they collide.
    main = FastMCP("Main")
    main.mount(english, namespace="en")
    main.mount(french, namespace="fr")

    print("mount(namespace=) ->", await names(main))
    async with Client(main) as c:
        print("  resource URI got a path segment:", [str(r.uri) for r in await c.list_resources()])
        print("  en_greet('Ada') ->", (await c.call_tool("en_greet", {"name": "Ada"})).data)
        print("  fr_greet('Ada') ->", (await c.call_tool("fr_greet", {"name": "Ada"})).data)

    # Namespace also works standalone, with no mounting involved.
    solo = FastMCP("Solo")

    @solo.tool
    def greet(name: str) -> str:  # noqa: F811
        return f"Hello, {name}!"

    solo.add_transform(Namespace("api"))
    print("add_transform(Namespace) ->", await names(solo))


# ================================================= 2. ToolTransform (deferred)
async def demo_tool_transform():
    """For tools arriving from somewhere you don't control."""
    upstream = FastMCP("Upstream")

    @upstream.tool
    def verbose_greeting_generator_v2(recipient_full_name: str) -> str:
        """Generates a greeting for the supplied recipient."""
        return f"Hello, {recipient_full_name}!"

    mcp = FastMCP("Main")
    mcp.mount(upstream)
    mcp.add_transform(
        ToolTransform(
            {
                "verbose_greeting_generator_v2": ToolTransformConfig(
                    name="greet",
                    description="Greets someone by name.",
                )
            }
        )
    )

    print("\nToolTransform ->", await names(mcp))
    async with Client(mcp) as c:
        r = await c.call_tool("greet", {"recipient_full_name": "Ada"})
        print("  greet('Ada') ->", r.data, "(ran the original function)")


# ============================================== 3. Tool.from_tool (immediate)
async def demo_from_tool():
    """For a tool object you hold, reshaped before registration."""

    # The standalone @tool decorator builds a Tool WITHOUT attaching it.
    @tool
    def greet(n: str, r: int = 1) -> str:
        """Greets someone."""
        return " ".join([f"Hello, {n}!"] * r)

    # rename cryptic parameters into something an LLM can guess
    better = Tool.from_tool(
        greet,
        name="greet_clearly",
        description="Greets someone by name, optionally repeating.",
        transform_args={
            "n": ArgTransform(name="name", description="Who to greet."),
            "r": ArgTransform(name="repeat", description="How many greetings."),
        },
    )

    @tool
    def greet_user(user_id: str, name: str) -> str:
        """Greets on behalf of a specific user account."""
        return f"Hello, {name}! (from user {user_id})"

    # hide=True removes an argument from the schema and injects a value.
    # default_factory generates a fresh one per call (and REQUIRES hide=True).
    current_user = "user-123"
    as_me = Tool.from_tool(
        greet_user,
        name="greet_as_me",
        description="Greets someone on your behalf. No need to specify a user ID.",
        transform_args={
            "user_id": ArgTransform(hide=True, default=current_user),
            "name": ArgTransform(examples=["Ada"]),
        },
    )

    @tool
    def greet_traced(request_id: str, name: str) -> str:
        """Greets with a correlation id."""
        return f"Hello, {name}! (req {request_id})"

    traced = Tool.from_tool(
        greet_traced,
        name="greet_with_trace",
        transform_args={
            "request_id": ArgTransform(hide=True, default_factory=lambda: str(uuid.uuid4())[:8]),
        },
    )

    # transform_fn wraps execution. Call forward() with the TRANSFORMED names;
    # it maps them back. (forward_raw() skips mapping -- original names.)
    @tool
    def greet_repeated(name: str, times: int) -> str:
        """Greets someone `times` times."""
        return " ".join([f"Hello, {name}!"] * times)

    async def safe_greet(name: str, count: int) -> str:
        if count < 1:
            # ToolError, not ValueError: a bare exception raised inside a
            # transform_fn escapes as a protocol-level "Internal server
            # error" rather than a tool error the client can read.
            raise ToolError("count must be at least 1")
        return await forward(name=name, count=count)

    guarded = Tool.from_tool(
        greet_repeated,
        name="greet_safely",
        transform_fn=safe_greet,
        transform_args={"times": ArgTransform(name="count")},
    )

    mcp = FastMCP("Reshaped")
    for t in (better, as_me, traced, guarded):
        mcp.add_tool(t)

    print("\nTool.from_tool ->", await names(mcp))
    async with Client(mcp) as c:
        tools = {t.name: t for t in await c.list_tools()}
        print("  greet_clearly args:", list(tools["greet_clearly"].input_schema["properties"]))
        print("  greet_as_me args  :", list(tools["greet_as_me"].input_schema["properties"]),
              "(user_id hidden)")

        print("  greet_as_me       ->", (await c.call_tool("greet_as_me", {"name": "Ada"})).data)
        print("  greet_with_trace  ->", (await c.call_tool("greet_with_trace", {"name": "Ada"})).data)
        print("  greet_safely x2   ->",
              (await c.call_tool("greet_safely", {"name": "Ada", "count": 2})).data)
        r = await c.call_tool("greet_safely", {"name": "Ada", "count": 0}, raise_on_error=False)
        print("  greet_safely x0   -> isError =", r.is_error, "(guard ran before forward)")


# ============================================ 4. ordering + a custom transform
class TagFilter(Transform):
    """Keep only tools carrying one of the required tags -- both patterns."""

    def __init__(self, required_tags: set[str]):
        self.required_tags = required_tags

    async def list_tools(self, tools: Sequence[Tool]) -> Sequence[Tool]:
        return [t for t in tools if t.tags & self.required_tags]

    async def get_tool(
        self, name: str, call_next: GetToolNext, *, version: VersionSpec | None = None
    ) -> Tool | None:
        # Accept the keyword-only `version` the server passes in fastmcp 4.x,
        # and hand it on -- omitting it raises TypeError at call time.
        t = await call_next(name, version=version)
        # returning None means "this name isn't mine"
        return t if t and t.tags & self.required_tags else None


async def demo_ordering_and_custom():
    sub = FastMCP("Sub")

    @sub.tool(tags={"public"})
    def verbose_greeting_generator(name: str) -> str:
        """Kept -- tagged public."""
        return f"Hello, {name}!"

    @sub.tool(tags={"internal"})
    def greet_debug(name: str) -> str:
        """Filtered out -- tagged internal."""
        return f"[debug] {name}"

    provider = FastMCPProvider(sub)
    provider.add_transform(Namespace("api"))                      # applied first
    provider.add_transform(                                       # sees api_ names
        ToolTransform({"api_verbose_greeting_generator": ToolTransformConfig(name="greet")})
    )

    main = FastMCP("Main", providers=[provider], transforms=[TagFilter({"public"})])

    print("\nordering: verbose_greeting_generator -> api_verbose_... -> greet")
    print("  plus a server-level custom TagFilter ->", await names(main))
    async with Client(main) as c:
        print("  greet('Ada') ->", (await c.call_tool("greet", {"name": "Ada"})).data)


async def main():
    await demo_namespace()
    await demo_tool_transform()
    await demo_from_tool()
    await demo_ordering_and_custom()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Swap the two provider.add_transform calls in demo_ordering_and_custom.
#    The ToolTransform now sees "verbose_greeting_generator" (no prefix) -- so
#    its key stops matching and the rename silently does nothing.
# 2. In TagFilter.get_tool, return the tool unconditionally. greet_debug
#    vanishes from list_tools but stays callable -- listing and access are
#    separate.
# 3. Write a Transform that upper-cases every tool description.
# 4. Use ArgTransform(required=True) to make `repeat` mandatory.
