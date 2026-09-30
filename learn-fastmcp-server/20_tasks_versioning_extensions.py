"""Lesson 20 -- Background tasks, versioning, extensions
========================================================

Three ways a server grows without a rewrite: run work in the background,
serve two generations of greet() at once, and add protocol features of
your own.

BACKGROUND TASKS (pip install 'fastmcp[tasks]')
You could already use asyncio for background work -- what tasks add is
COORDINATION IN THE PROTOCOL, so any tasks-aware client can start, poll and
collect the result the standard way.
    mcp.add_extension(TasksExtension())   makes background execution possible
    @mcp.tool(task=True)                  opts ONE tool into it
    (task=True with no extension added fails at server startup)

VERSIONING
One tool name, several implementations. Clients get the highest version by
default, or can ask for a specific one with call_tool(..., version="1.0").
You can't mix versioned and unversioned tools under the same name.

EXTENSIONS
A custom protocol capability, named like a reverse-DNS string, that both
client and server agree to support. FastMCP advertises it and routes calls
to it, but does not filter who can use it -- that check is on you.

Run:  uv run python 20_tasks_versioning_extensions.py
"""

import asyncio
from typing import Any

from fastmcp import Client, Context, FastMCP
from fastmcp.dependencies import Progress
from fastmcp.server.extensions import MethodBinding, ServerExtension
from fastmcp.server.providers import LocalProvider
from fastmcp.server.transforms import VersionFilter
from fastmcp.utilities.tasks import TaskConfig
from fastmcp_tasks import TasksExtension
from mcp.types import RequestParams


# ============================================================ 1. versioning
async def demo_versioning():
    mcp = FastMCP("GreetingService")

    @mcp.tool(version="1.0")
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    @mcp.tool(version="2.0")
    def greet(name: str, language: str = "en") -> str:  # noqa: F811 -- same name, new version
        """Greets someone by name, in a language."""
        hello = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}.get(language, "Hello")
        return f"{hello}, {name}!"

    async with Client(mcp) as c:
        tools = await c.list_tools()
        print("client sees one greet (duplicates collapse):", [t.name for t in tools])

        # version metadata rides along under meta.fastmcp
        meta = (tools[0].meta or {}).get("fastmcp", {})
        print("  version   :", meta.get("version"), "(the highest)")
        print("  versions  :", meta.get("versions"), "(highest first)")

        print("\n  default call (highest) ->", (await c.call_tool("greet", {"name": "Ada"})).data)
        print("  version='1.0'          ->",
              (await c.call_tool("greet", {"name": "Ada"}, version="1.0")).data)
        r = await c.call_tool("greet", {"name": "Ada", "language": "fr"}, version="2.0")
        print("  version='2.0' + lang   ->", r.data)

    # server-side retrieval takes a version too
    print("\n  get_tool('greet').version         ->", (await mcp.get_tool("greet")).version)
    print("  get_tool('greet', version='1.0')  ->",
          (await mcp.get_tool("greet", version="1.0")).version)

    # A generic MCP client asks for a version through params._meta:
    #   {"name": "greet", "arguments": {...},
    #    "_meta": {"fastmcp": {"version": "1.0"}}}
    # _meta sits in params, not arguments, so your function never sees it.

    # ---- two API surfaces from ONE shared provider
    components = LocalProvider()

    @components.tool(version="1.0")
    def greet(name: str) -> str:  # noqa: F811
        """v1."""
        return f"Hello, {name}!"

    @components.tool(version="2.0")
    def greet(name: str, language: str = "en") -> str:  # noqa: F811
        """v2."""
        return f"[{language}] Hello, {name}!"

    api_v1 = FastMCP("API v1", providers=[components])
    api_v1.add_transform(VersionFilter(version_lt="2.0"))

    api_v2 = FastMCP("API v2", providers=[components])
    api_v2.add_transform(VersionFilter(version_gte="2.0"))

    async with Client(api_v1) as c:
        print("\n  api_v1 (version_lt='2.0')  ->", (await c.call_tool("greet", {"name": "Ada"})).data)
    async with Client(api_v2) as c:
        print("  api_v2 (version_gte='2.0') ->", (await c.call_tool("greet", {"name": "Ada"})).data)

    # unversioned components pass the filter by default; include_unversioned=False drops them

    # ---- you cannot mix the two styles under one name
    mixed = FastMCP("Mixed")

    @mixed.tool
    def farewell(name: str) -> str:
        """Unversioned."""
        return f"Goodbye, {name}!"

    try:
        @mixed.tool(version="2.0")
        def farewell(name: str) -> str:  # noqa: F811
            """Versioned -- rejected."""
            return f"Farewell, {name}!"
    except ValueError as e:
        print("\n  mixing versioned + unversioned ->", str(e)[-52:])

    # removal is per-version, or all versions at once
    mcp.local_provider.remove_tool("greet", version="1.0")
    print("  after remove_tool(version='1.0') -> versions left:",
          [t.version for t in await mcp.list_tools()])

    print(
        "\n  version strings compare like real version numbers, not plain text:\n"
        "  '1' < '2' < '10' and '1.9' < '1.10' (not string order, which would\n"
        "  put '1.10' before '1.9').\n"
    )


# ========================================================= 2. background tasks
async def demo_tasks():
    mcp = FastMCP("GreetingService")
    # The extension does the executing. Defaults to the memory:// backend and
    # starts an EMBEDDED worker -- no separate process needed.
    # Production: TasksExtension(url="redis://localhost:6379/0", concurrency=20)
    mcp.add_extension(TasksExtension())

    @mcp.tool(task=True)                    # == TaskConfig(mode="optional")
    async def greet_everyone(names: list[str], progress: Progress = Progress()) -> str:
        """Greet a long list of people in the background."""
        await progress.set_total(len(names))
        for name in names:
            await progress.set_message(f"Greeting {name}")
            await asyncio.sleep(0.01)
            await progress.increment()
        return f"Greeted {len(names)} people"

    @mcp.tool(task=TaskConfig(mode="required"))
    async def greet_the_world() -> str:
        """Background only -- errors if the client didn't opt in."""
        return "Hello, world!"

    @mcp.tool(task=TaskConfig(mode="forbidden"))
    async def greet(name: str) -> str:
        """Never backgrounded."""
        return f"Hello, {name}!"

    async with Client(mcp) as c:
        print("task modes on one server:", sorted(t.name for t in await c.list_tools()))

        # From a FastMCP client this looks identical either way -- it starts the
        # task, polls, and returns the result for you.
        r = await c.call_tool("greet_everyone", {"names": ["Ada", "Bob", "Cleo"]})
        print("  greet_everyone (optional) ->", r.data)
        r = await c.call_tool("greet_the_world", {})
        print("  greet_the_world (required)->", r.data)
        r = await c.call_tool("greet", {"name": "Ada"})
        print("  greet (forbidden)         ->", r.data)

    print(
        "\n  backends: memory:// (default) is single-process and loses pending\n"
        "  tasks on restart. redis:// survives restarts and lets workers spread\n"
        "  across machines.\n"
        "\n  A task outlives its own request, so FastMCP snapshots the caller's\n"
        "  credentials to restore them in the worker later -- set\n"
        "  FASTMCP_TASKS_ENCRYPTION_KEY in production so that snapshot isn't\n"
        "  stored in plaintext.\n"
        "\n  Restrictions: async functions only; tools only (not resources or\n"
        "  prompts); ctx.elicit() doesn't work inside a task (use the guard\n"
        "  pattern from lesson 15 instead).\n"
    )


# ============================================================ 3. extensions
class GreetCounterParams(RequestParams):
    """Params model for our new wire method. Subclass RequestParams so _meta parses."""


class GreetCounterExtension(ServerExtension):
    """Counts greet() calls and exposes the count over a method of its own.

    `identifier` must look like reverse-DNS ("vendor-prefix/name") -- this
    is checked as soon as the class is defined, not later at connect time.
    """

    identifier = "com.example/greet-counter"

    def __init__(self) -> None:
        self.count = 0

    def settings(self) -> dict[str, Any]:
        """Surfaces on the wire at capabilities.extensions[identifier]."""
        return {"countsTools": ["greet"], "resettable": False}

    def methods(self) -> list[MethodBinding]:
        """STRICTLY ADDITIVE -- binding a spec method like tools/call raises."""
        return [
            MethodBinding(
                method="greetCounter/get",
                params_type=GreetCounterParams,
                handler=self.get_count,
            )
        ]

    async def get_count(self, ctx, params: GreetCounterParams) -> dict[str, Any]:
        return {"count": self.count}

    async def intercept_tool_call(self, params, context, call_next):
        """The last gate before the tool body runs -- after all middleware.

        Fires for EVERY tool call, even from clients that never advertised
        this extension (client_extension_settings() returns None for them).
        Counting is harmless regardless, so we let everyone through -- but
        if you ever short-circuit here, check that setting first, or you'll
        hand an unaware client a result shape it can't understand.
        """
        if context.client_extension_settings(self.identifier) is None:
            return await call_next()
        if params.name == "greet":
            self.count += 1
        return await call_next()


async def demo_extensions():
    mcp = FastMCP("GreetingService")
    ext = GreetCounterExtension()
    # Must be registered BEFORE startup: adding one mid-lifespan raises,
    # because its own lifespan could no longer run.
    mcp.add_extension(ext)

    @mcp.tool
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    async with Client(mcp) as c:
        caps = c.server_capabilities.extensions or {}
        print("\nadvertised extensions:", list(caps))
        print("  our settings:", caps.get("com.example/greet-counter"))

        for name in ("Ada", "Bob", "Cleo"):
            await c.call_tool("greet", {"name": name})
        print("  3 greet calls; interceptor counted:", ext.count,
              "(0 -> this client never negotiated the extension)")

    print(
        "\n  a few more details:\n"
        "    an extension can have its own lifespan(), just like the server\n"
        "    multiple interceptors nest, first registered is outermost\n"
        "    a mounted CHILD server's extensions do not bubble up to the parent\n"
        "  Client side: Client(extensions=[advertise('com.example/uploads', {...})])\n"
    )


async def main():
    await demo_versioning()
    await demo_tasks()
    await demo_extensions()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Add greet version="10.0" and confirm it beats "2.0" -- PEP 440 compares
#    numerically, so it is not string order.
# 2. Call client.call_tool("greet", version="9.9") -- NotFoundError, not a
#    silent fallback to the highest.
# 3. Put VersionFilter(version_gte="2.0", include_unversioned=False) on a
#    server that also has unversioned tools. They disappear.
# 4. Put task=True on a SYNC function -- rejected at registration.
# 5. Remove mcp.add_extension(TasksExtension()) but keep task=True. The server
#    fails at STARTUP, not at call time.
# 6. Give GreetCounterExtension a bad identifier ("greet-counter", no prefix)
#    and watch it fail the moment the class is defined.
# 7. Bind "tools/call" in methods() and read the construction error.
