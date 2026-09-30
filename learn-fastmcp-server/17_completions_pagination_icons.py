"""Lesson 17 -- Completions, pagination, icons: three client-UI features
========================================================================

None of these change what your server can DO -- they change how a client
can present it: suggest values while typing, hand over a huge catalog in
chunks, and show a recognisable picture. Still just greeting people.

    COMPLETIONS  @mcp.completion (one handler per server)
    As the user types a prompt or resource-template argument, the client
    asks for suggestions; you return a list of candidate strings.

    PAGINATION  FastMCP(list_page_size=N)
    Off by default -- everything arrives in one response. Set a positive
    int and list calls start returning pages with a cursor to fetch the
    next one. Only worth it above roughly 100 components.

    ICONS  icons=[Icon(src=...)]
    A picture for the server, a tool, a resource, or a prompt. Only `src`
    is required; `theme="light"|"dark"` lets you swap variants so a dark
    logo doesn't vanish into a dark sidebar.

Run:  uv run python 17_completions_pagination_icons.py
"""

import asyncio

from fastmcp import Client, FastMCP
from fastmcp.server.dependencies import get_context
from fastmcp.utilities.types import Image  # noqa: F401 -- used in the icons notes
from mcp.types import Completion, Icon, PromptReference, ResourceTemplateReference

# ============================================================ 1. completions
comp = FastMCP("GreetingService")

NAMES_BY_TEAM = {
    "engineering": ["ada", "alan", "grace"],
    "design": ["dieter", "paula"],
}
LANGUAGES = ["en", "es", "de", "fr", "fi"]


@comp.prompt
def ask_greeting(language: str) -> str:
    """Ask for a greeting in a given language."""
    return f"Write a greeting in {language}."


@comp.prompt
def greet_in_style(style: str) -> str:
    """Ask for a greeting in a given style."""
    return f"Write a {style} greeting."


@comp.resource("greet://{team}/{person}")
def greeting_for(team: str, person: str) -> str:
    """A ready-made greeting for someone on a team."""
    return f"Hello, {person} from {team}!"


# ONE handler serves every component, so branch on `ref` first, then argument.
@comp.completion
async def complete(ref, argument, context):
    ctx = get_context()
    await ctx.debug(f"completing {argument.name!r} = {argument.value!r}")

    if isinstance(ref, PromptReference):
        if ref.name == "greet_in_style" and argument.name == "style":
            options = ["formal", "friendly", "funny"]
            # always filter against what's typed so far
            return [o for o in options if o.startswith(argument.value)]

        if ref.name == "ask_greeting" and argument.name == "language":
            matches = [c for c in LANGUAGES if c.startswith(argument.value)]
            # Completion() when you may exceed the protocol's 100-value cap:
            # `total` is how many exist, `has_more` says you truncated.
            return Completion(
                values=matches[:100], total=len(matches), has_more=len(matches) > 100
            )

    if isinstance(ref, ResourceTemplateReference):
        if ref.uri == "greet://{team}/{person}" and argument.name == "person":
            # context holds arguments the user ALREADY filled in -- but it is
            # None until at least one is resolved, so guard it.
            team = context.arguments.get("team") if context and context.arguments else None
            people = NAMES_BY_TEAM.get(team or "", [])
            return [p for p in people if p.startswith(argument.value)]

    return None          # unrecognised ref -> the client sees an empty list


async def demo_completions():
    async with Client(comp) as c:
        print("completions capability advertised:", c.server_capabilities.completions is not None)

        r = await c.complete(PromptReference(type="ref/prompt", name="greet_in_style"),
                             {"name": "style", "value": "f"})
        print('  greet_in_style style="f"  ->', r.values)

        r = await c.complete(PromptReference(type="ref/prompt", name="ask_greeting"),
                             {"name": "language", "value": "f"})
        print('  ask_greeting language="f" ->', r.values, f"(total={r.total}, has_more={r.has_more})")

        # dependent completion: which people you can greet depends on the team
        ref = ResourceTemplateReference(type="ref/resource", uri="greet://{team}/{person}")
        r = await c.complete(ref, {"name": "person", "value": ""},
                             context_arguments={"team": "engineering"})
        print("  person (team=engineering) ->", r.values)
        r = await c.complete(ref, {"name": "person", "value": "a"},
                             context_arguments={"team": "engineering"})
        print('  person (team=eng, "a")    ->', r.values)
        r = await c.complete(ref, {"name": "person", "value": ""})
        print("  person (no team yet)      ->", r.values, "(context was None)")

    # Note: completions bypass per-component visibility/auth rules, since
    # FastMCP never resolves the named component here -- it just calls your
    # handler. If the candidate VALUES themselves are sensitive, check the
    # auth context yourself (get_context()) and return None when unauthorized.


# ============================================================= 2. pagination
async def demo_pagination():
    paged = FastMCP("GreetingRegistry", list_page_size=50)

    # 120 per-locale greeting tools, as if generated from a locale table
    for i in range(120):
        paged.tool(name=f"greet_locale_{i:03d}")(lambda: "ok")

    async with Client(paged) as c:
        # the convenience method walks every page and merges
        tools = await c.list_tools()
        print(f"\nlist_page_size=50, 120 tools -> list_tools() returned {len(tools)}")

        # manual paging, for memory limits, progress reporting or early exit
        page = await c.list_tools_mcp()
        n, pages = len(page.tools), 1
        print(f"  page {pages}: {len(page.tools)} tools, cursor={page.next_cursor!r}")
        while page.next_cursor:
            page = await c.list_tools_mcp(cursor=page.next_cursor)
            pages += 1
            n += len(page.tools)
            print(f"  page {pages}: {len(page.tools)} tools, cursor={page.next_cursor!r}")
        print(f"  {pages} pages, {n} tools; next_cursor=None means the end")

    # One page size governs every list endpoint (tools, resources, prompts).
    # The same manual _mcp pattern also works for the other three.


# ================================================================== 3. icons
def build_icon_server() -> FastMCP:
    # Several resolutions: the client picks what suits its display.
    server_icons = [
        Icon(src="https://greetings.example.com/icon-48.png", mime_type="image/png", sizes=["48x48"]),
        Icon(src="https://greetings.example.com/icon-96.png", mime_type="image/png", sizes=["96x96"]),
    ]

    mcp = FastMCP(
        name="GreetingService",
        website_url="https://greetings.example.com",
        icons=server_icons,
    )

    # theme variants -- so a dark logo doesn't disappear into a dark sidebar
    @mcp.tool(
        icons=[
            Icon(src="https://example.com/greet-light.png", theme="light"),
            Icon(src="https://example.com/greet-dark.png", theme="dark"),
        ]
    )
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    # a data URI embeds the image: no hosting, always available
    inline_svg = (
        "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdp"
        "ZHRoPSIyNCIgaGVpZ2h0PSIyNCI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDgg"
        "MTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6Ii8+PC9zdmc+"
    )

    @mcp.tool(icons=[Icon(src=inline_svg, mime_type="image/svg+xml")])
    def farewell(name: str) -> str:
        """Says goodbye -- with an embedded SVG icon."""
        return f"Goodbye, {name}!"

    @mcp.resource("data://greeting-config",
                  icons=[Icon(src="https://example.com/config-icon.png")])
    def greeting_config() -> dict:
        """The greeting templates this server knows."""
        return {"language": "en"}

    @mcp.resource("greet://{name}", icons=[Icon(src="https://example.com/person-icon.png")])
    def greeting_for(name: str) -> dict:
        """A ready-made greeting for someone."""
        return {"greeting": f"Hello, {name}!"}

    @mcp.prompt(icons=[Icon(src="https://example.com/prompt-icon.png")])
    def ask_greeting(name: str) -> str:
        """Ask for a greeting."""
        return f"Write a greeting for {name}."

    return mcp


async def demo_icons():
    mcp = build_icon_server()

    async with Client(mcp) as c:
        info = c.server_info
        print("\nserver icons:", [(i.src.split('/')[-1], i.sizes) for i in info.icons])
        print("website_url :", info.website_url)

        for t in await c.list_tools():
            print(f"  tool {t.name:<10}",
                  [(i.src.split('/')[-1][:24], i.theme) for i in (t.icons or [])])
        for r in await c.list_resources():
            print(f"  resource {str(r.uri):<24}", [i.src.split('/')[-1] for i in (r.icons or [])])
        for t in await c.list_resource_templates():
            print(f"  template {t.uri_template:<24}", [i.src.split('/')[-1] for i in (t.icons or [])])
        for p in await c.list_prompts():
            print(f"  prompt {p.name:<12}", [i.src.split('/')[-1] for i in (p.icons or [])])

    print(
        "\n  from a local file:  Icon(src=Image(path='./favicon.png').to_data_uri())\n"
        "  icons is ALWAYS a list, even for one icon. Only src is required.\n"
        "  Rendering is entirely up to the client -- FastMCP only advertises it."
    )


async def main():
    await demo_completions()
    await demo_pagination()
    await demo_icons()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Delete the @comp.completion handler and re-check server_capabilities.
#    completions -- a server with no handler never advertises the capability,
#    so careful clients skip completion calls entirely.
# 2. Return a bare list instead of Completion() from ask_greeting. You lose
#    total/has_more, so the client can't tell the list was truncated.
# 3. Stop filtering on argument.value and watch suggestions stop narrowing
#    as you type.
# 4. Set list_page_size=7 and count the pages for 120 tools.
# 5. Try to build a cursor by hand. It is opaque on purpose -- its contents
#    are an implementation detail that may change.
# 6. Give one tool a single themeless icon and one tool light/dark variants,
#    then open the server in a client with a dark UI.
