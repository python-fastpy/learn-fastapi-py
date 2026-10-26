"""Tasks, versioning, extensions -- growing a server without a rewrite
=============================================================================

BACKGROUND TASKS (fastmcp[tasks])
    client ── call ──► server replies at once with a task id
           ── poll ──► "working" ... "completed"
           ── get  ──► the result          (a FastMCP client polls for you)

    mcp.add_extension(TasksExtension())    required, or task=True fails at startup
    @mcp.tool(task=True)                   optional | TaskConfig(mode="required" / "forbidden")
    progress: Progress = Progress()        set_total / set_message / increment
    production: TasksExtension(url="redis://..."), set FASTMCP_TASKS_ENCRYPTION_KEY
    async tools only; use 05's guard pattern, not ctx.elicit()

VERSIONING -- one name, several implementations
    @mcp.tool(version="1.0") / (version="2.0")   clients get the highest by default
    call_tool(..., version="1.0")                pick one ("1.9" < "1.10" -- numeric)
    VersionFilter(version_lt="2.0")              a v1-only API surface
    can't mix versioned + unversioned tools under one name

EXTENSIONS -- a custom protocol capability ("com.example/name")
    settings()             advertised in capabilities.extensions
    methods()              NEW wire methods only
    intercept_tool_call()  runs before every tool -- check the client opted in

Client side of tasks: ../../client/advanced/06_tasks.py

Level: ADVANCED
Run:  uv run python advanced/11_tasks_versioning_extensions.py      (from mcp/server)
"""

import asyncio

from fastmcp import Client, FastMCP
from fastmcp.dependencies import Progress
from fastmcp.server.extensions import MethodBinding, ServerExtension
from fastmcp.server.transforms import VersionFilter
from fastmcp.utilities.tasks import TaskConfig
from fastmcp_tasks import TasksExtension
from mcp.types import RequestParams


# ============================================================ 1. tasks
async def demo_tasks():
    mcp = FastMCP("Greetings")
    mcp.add_extension(TasksExtension())

    @mcp.tool(task=True)
    async def greet_everyone(names: list[str], progress: Progress = Progress()) -> str:
        await progress.set_total(len(names))
        for name in names:
            await progress.set_message(f"greeting {name}")
            await progress.increment()
        return f"Greeted {len(names)} people"

    @mcp.tool(task=TaskConfig(mode="forbidden"))
    async def greet(name: str) -> str:
        return f"Hello, {name}!"

    async with Client(mcp) as c:
        print("background ->", (await c.call_tool("greet_everyone", {"names": ["Ada", "Bob"]})).data)
        print("forbidden  ->", (await c.call_tool("greet", {"name": "Ada"})).data)


# ======================================================= 2. versioning
async def demo_versioning():
    mcp = FastMCP("Greetings")
    mcp.tool(lambda name: f"Hello, {name}!", name="greet", version="1.0")
    mcp.tool(lambda name: f"Bonjour, {name}!", name="greet", version="2.0")

    async with Client(mcp) as c:
        print("\ndefault    ->", (await c.call_tool("greet", {"name": "Ada"})).content[0].text)
        print("v1.0       ->", (await c.call_tool("greet", {"name": "Ada"}, version="1.0")).content[0].text)

    mcp.add_transform(VersionFilter(version_lt="2.0"))
    async with Client(mcp) as c:
        print("v1 surface ->", (await c.call_tool("greet", {"name": "Ada"})).content[0].text)


# ======================================================= 3. extensions
class CounterParams(RequestParams):
    pass


class GreetCounter(ServerExtension):
    identifier = "com.example/greet-counter"        # checked when the class is defined

    def __init__(self):
        self.count = 0

    def settings(self):
        return {"countsTools": ["greet"]}

    def methods(self):
        return [MethodBinding(method="greetCounter/get", params_type=CounterParams,
                              handler=lambda ctx, params: {"count": self.count})]

    async def intercept_tool_call(self, params, context, call_next):
        if context.client_extension_settings(self.identifier) is not None and params.name == "greet":
            self.count += 1                          # only for clients that opted in
        return await call_next()


async def demo_extensions():
    mcp = FastMCP("Greetings")
    ext = GreetCounter()
    mcp.add_extension(ext)                           # before startup
    mcp.tool(lambda name: f"Hello, {name}!", name="greet")
    async with Client(mcp) as c:
        await c.call_tool("greet", {"name": "Ada"})
        print("\nadvertised ->", list(c.server_capabilities.extensions or {}))
        print("counted    ->", ext.count, "(this client didn't opt in)")


async def main():
    await demo_tasks()
    await demo_versioning()
    await demo_extensions()


if __name__ == "__main__":
    asyncio.run(main())
