"""Lesson 14 -- Composing servers
=================================

Split a big application into focused servers, then combine them with
mount(). It's a LIVE link: the parent asks the child at request time, so a
tool added to the child after mounting is immediately reachable through
the parent -- no re-mounting needed.

Here the children are per-language greeting servers, which makes the name
collision (both export `greet`) the natural thing to solve with namespaces:

    main.mount(english, namespace="en")
    main.mount(french,  namespace="fr")

    NAMESPACING            without          with namespace="en"
    tool                   greet            en_greet
    resource                data://greeting  data://en/greeting
    custom_route            /health          /health   (NOT namespaced!)

CONFLICTS: with no namespace and the same name, the FIRST mount wins.

COST: every parent-level list_tools() call fans out to every child. A local
child is fast; a remote, HTTP-proxied child is much slower and that delay
lands on the parent. Keep the tree shallow, or cache.

NOTE ON A SECOND WAY TO DO THIS: learn-mcp lesson 11 solves the same
"which server owns this tool" problem by hand-rolling a ServerRegistry
instead of mount()ing. That's the pattern a real production backend
tends to reach for once it also needs per-server health checks and a
capability cache that mount() doesn't give you -- mount() here is less
code when you don't need that.

Run:  uv run python 14_composition.py
"""

import asyncio

from fastmcp import Client, FastMCP
from fastmcp.server import create_proxy
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


# ============================================================ 1. basic mount
async def demo_basic():
    english = FastMCP("English")

    @english.tool
    def greet(name: str) -> str:
        """Greets someone in English."""
        return f"Hello, {name}!"

    @english.resource("data://greeting")
    def greeting_template() -> str:
        """The English greeting template."""
        return "Hello, {name}!"

    @english.prompt
    def ask_greeting(name: str) -> str:
        """Ask for an English greeting."""
        return f"Write an English greeting for {name}."

    main = FastMCP("GreetingService")
    main.mount(english)

    async with Client(main) as c:
        print("mount(), no namespace")
        print("  tools     :", [t.name for t in await c.list_tools()])
        print("  resources :", [str(r.uri) for r in await c.list_resources()])
        print("  prompts   :", [p.name for p in await c.list_prompts()])
        print("  call      ->", (await c.call_tool("greet", {"name": "Ada"})).data)


# ========================================================= 2. live, not a copy
async def demo_dynamic():
    child = FastMCP("English")

    @child.tool
    def greet(name: str) -> str:
        """Registered before mounting."""
        return f"Hello, {name}!"

    main = FastMCP("GreetingService")
    main.mount(child, namespace="en")

    async with Client(main) as c:
        print("\nbefore adding:", sorted(t.name for t in await c.list_tools()))

    # added AFTER the mount call -- no re-mount, no restart
    @child.tool
    def farewell(name: str) -> str:
        """Added after mounting!"""
        return f"Goodbye, {name}!"

    async with Client(main) as c:
        print("after adding :", sorted(t.name for t in await c.list_tools()))
        print("  call       ->", (await c.call_tool("en_farewell", {"name": "Ada"})).data)


# ========================================================= 3. namespaces
async def demo_namespace():
    english, french = FastMCP("English"), FastMCP("French")

    @english.tool
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    @english.resource("data://greeting")
    def en_template() -> str:
        return "Hello, {name}!"

    @english.resource("greet://{name}")
    def en_for(name: str) -> str:
        return f"Hello, {name}!"

    @french.tool
    def greet(name: str) -> str:  # noqa: F811 -- the collision is the point
        return f"Bonjour, {name}!"

    main = FastMCP("GreetingService")
    main.mount(english, namespace="en")
    main.mount(french, namespace="fr")

    async with Client(main) as c:
        print("\ntwo children, same tool name")
        print("  tools     :", sorted(t.name for t in await c.list_tools()))
        print("  resources :", [str(r.uri) for r in await c.list_resources()], "(path segment)")
        print("  templates :", [t.uri_template for t in await c.list_resource_templates()])
        print("  en_greet  ->", (await c.call_tool("en_greet", {"name": "Ada"})).data)
        print("  fr_greet  ->", (await c.call_tool("fr_greet", {"name": "Ada"})).data)
        print("  read data://en/greeting ->",
              (await c.read_resource("data://en/greeting"))[0].text)


# ================================================== 4. conflicts, no namespace
async def demo_conflict():
    english, french = FastMCP("English"), FastMCP("French")

    @english.tool
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    @french.tool
    def greet(name: str) -> str:  # noqa: F811
        return f"Bonjour, {name}!"

    main = FastMCP("GreetingService")
    main.mount(english)          # registered first
    main.mount(french)

    @main.tool
    def greet_local(name: str) -> str:
        """LocalProvider is always slot 0."""
        return f"Hello from main, {name}!"

    async with Client(main) as c:
        print("\nno namespace, same name -> first mount wins:",
              (await c.call_tool("greet", {"name": "Ada"})).data)


# ============================================= 5. tag filtering through mount
async def demo_tag_filtering():
    """One shared child, two deployment surfaces."""
    greetings = FastMCP("Greetings")

    @greetings.tool(tags={"production"})
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    @greetings.tool(tags={"development"})
    def greet_debug(name: str) -> str:
        return f"[debug] greet({name!r})"

    prod_app = FastMCP("Production")
    prod_app.mount(greetings, namespace="api")
    prod_app.enable(tags={"production"}, only=True)   # parent filters the child

    dev_app = FastMCP("Development")
    dev_app.mount(greetings, namespace="api")

    async with Client(prod_app) as c:
        print("\nprod surface:", sorted(t.name for t in await c.list_tools()))
    async with Client(dev_app) as c:
        print("dev surface :", sorted(t.name for t in await c.list_tools()))


# ============================================ 6. custom routes are NOT prefixed
async def demo_custom_routes():
    child = FastMCP("English")

    @child.tool
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    @child.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> Response:
        return JSONResponse({"status": "ok"})

    main = FastMCP("GreetingService")
    main.mount(child, namespace="en")

    async with Client(main) as c:
        print("\nchild tool IS namespaced     :", [t.name for t in await c.list_tools()])

    routes = sorted(r.path for r in main.http_app().routes if getattr(r, "path", None))
    print("child route is NOT namespaced:", routes, "(/health, not /en/health)")


# ========================================== 7. mounting an external server
async def demo_external():
    """Remote servers and separate scripts mount via create_proxy()."""
    external = FastMCP("RemoteGreeter")

    @external.tool
    def greet(name: str) -> str:
        """Lives in another process, conceptually."""
        return f"Hello from the remote server, {name}!"

    main = FastMCP("GreetingService")

    @main.tool
    def greet_local(name: str) -> str:
        return f"Hello from main, {name}!"

    main.mount(create_proxy(external), namespace="remote")

    async with Client(main) as c:
        print("\nlocal + proxied:", sorted(t.name for t in await c.list_tools()))
        print("  remote_greet ->", (await c.call_tool("remote_greet", {"name": "Ada"})).data)

    print(
        "\n  create_proxy() also accepts a URL, a Path to a script, a config\n"
        "  dict, or a transport object -- not just a FastMCP instance.\n"
    )


async def main():
    await demo_basic()
    await demo_dynamic()
    await demo_namespace()
    await demo_conflict()
    await demo_tag_filtering()
    await demo_custom_routes()
    await demo_external()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Swap the mount order in demo_conflict -- "Bonjour" now wins.
# 2. Give french's greet version="2". Version beats registration order, so
#    French wins regardless of mount order.
# 3. Mount a server into a server into a server, then time list_tools().
# 4. In demo_tag_filtering, add a tool with NO tags and re-check prod_app:
#    only=True hides untagged components too.
