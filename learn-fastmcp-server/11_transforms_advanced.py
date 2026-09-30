"""Lesson 11 -- Big catalogs and tool-only clients
=================================================

Four transforms that change the SHAPE of your server's surface, not its
names. The catalog below is five greeting tools standing in for five hundred.

PROBLEM 1: 500 tools in tools/list burns tokens and confuses tool selection.
-> Tool Search: list_tools() returns just two tools instead --
   search_tools(query) to find candidates, call_tool(name, args) to run one.
   The real tools stay callable, just hidden from the listing.

PROBLEM 2: every intermediate result flows back through the model, wasting
tokens on data the model never needed to see.
-> Code Mode: the LLM writes Python that chains several tool calls together
   in a sandbox and returns only the final answer.

PROBLEM 3: some clients support ONLY tools -- no resources, no prompts.
-> ResourcesAsTools / PromptsAsTools: wraps resources and prompts as tools,
   so a tools-only client can still reach them.

Run:  uv run python 11_transforms_advanced.py
"""

import asyncio
import json
import textwrap
from collections.abc import Callable
from typing import Any

from fastmcp import Client, FastMCP
from fastmcp.experimental.transforms.code_mode import CodeMode
from fastmcp.server.transforms import PromptsAsTools, ResourcesAsTools, Visibility
from fastmcp.server.transforms.search import BM25SearchTransform, RegexSearchTransform


def found(result) -> list[str]:
    """Tool names in a search_tools result. An empty result has no content."""
    if not result.content:
        return []
    return [t["name"] for t in json.loads(result.content[0].text)]


def build_catalog(name: str) -> FastMCP:
    mcp = FastMCP(name)

    @mcp.tool
    def greet(name: str) -> str:
        """Greets someone by name in English."""
        return f"Hello, {name}!"

    @mcp.tool
    def translate_greeting(text: str, language: str) -> str:
        """Translates a greeting into another language."""
        return f"[{language}] {text}"

    @mcp.tool
    def delete_greeting(greeting_id: str) -> bool:
        """Deletes a saved greeting from the database by its ID."""
        return True

    @mcp.tool(tags={"admin"})
    def reset_all_greetings() -> str:
        """Admin-only: wipe every saved greeting."""
        return "wiped"

    @mcp.tool
    def help_() -> str:
        """Show help for the greeting server."""
        return "help text"

    return mcp


# ======================================================== 1. regex search
async def demo_regex():
    mcp = build_catalog("Regex")
    mcp.add_transform(
        RegexSearchTransform(
            max_results=10,                     # default cap is 5
            always_visible=["help_"],           # pinned: listed AND callable
            # search_tool_name="find_tools",    # rename to dodge collisions
            # call_tool_name="run_tool",
        )
    )

    async with Client(mcp) as c:
        print("list_tools now:", sorted(t.name for t in await c.list_tools()))

        r = await c.call_tool("search_tools", {"pattern": "greeting"})
        print("  pattern 'greeting'        ->", found(r))

        r = await c.call_tool("search_tools", {"pattern": "translate|language"})
        print("  pattern 'translate|lang'  ->", found(r))

        # the proxy runs a discovered tool through the normal pipeline
        r = await c.call_tool("call_tool", {"name": "greet", "arguments": {"name": "Ada"}})
        print("  call_tool(greet)          ->", r.content[0].text)

        # hidden from the listing, still directly callable
        r = await c.call_tool("delete_greeting", {"greeting_id": "7"})
        print("  direct delete_greeting    ->", r.content[0].text, "(hidden != inaccessible)")


# ========================================================== 2. BM25 search
async def demo_bm25():
    mcp = build_catalog("BM25")
    # Visibility runs first, so admin tools never reach the search index.
    mcp.add_transform(Visibility(False, tags={"admin"}))
    mcp.add_transform(BM25SearchTransform(max_results=3))

    async with Client(mcp) as c:
        r = await c.call_tool(
            "search_tools", {"query": "tools for removing saved greetings from the database"}
        )
        print("\nBM25 natural-language query ->", found(r), "(ranked by relevance)")

        # reset_all_greetings was disabled before the index was built, so no
        # query can surface it -- search honours the visibility pipeline.
        r = await c.call_tool("search_tools", {"query": "admin reset wipe everything"})
        print("  after Visibility(False, admin) ->", found(r) or "no matches")


# ============================================= 3. resources / prompts as tools
async def demo_as_tools():
    mcp = FastMCP("ToolOnly")

    @mcp.resource("data://greeting-config")
    def greeting_config() -> str:
        """The greeting templates this server knows."""
        return '{"en": "Hello, {name}!", "default": "en"}'

    @mcp.resource("greet://{name}")
    def greeting_for(name: str) -> str:
        """Get a ready-made greeting for someone."""
        return f'{{"greeting": "Hello, {name}!"}}'

    @mcp.prompt
    def ask_greeting(name: str, language: str = "en") -> str:
        """Asks the LLM to write a greeting."""
        return f"Write a greeting for {name} in {language}."

    # Pass the SERVER, not a provider.
    mcp.add_transform(ResourcesAsTools(mcp))
    mcp.add_transform(PromptsAsTools(mcp))

    async with Client(mcp) as c:
        print("\nas-tools generated:", sorted(t.name for t in await c.list_tools()))

        r = await c.call_tool("list_resources", {})
        listing = json.loads(r.content[0].text)
        print("  list_resources ->")
        for item in listing:
            # static resources carry "uri"; templates carry "uri_template"
            kind = "uri" if "uri" in item else "uri_template"
            print(f"    {kind:<13} {item[kind]}")

        r = await c.call_tool("read_resource", {"uri": "data://greeting-config"})
        print("  read static    ->", r.data)
        r = await c.call_tool("read_resource", {"uri": "greet://Ada"})
        print("  read template  ->", r.data, "(name extracted from the URI)")

        r = await c.call_tool("list_prompts", {})
        print("  list_prompts   ->", [p["name"] for p in json.loads(r.content[0].text)])
        r = await c.call_tool(
            "get_prompt", {"name": "ask_greeting", "arguments": {"name": "Ada", "language": "fr"}}
        )
        print("  get_prompt     ->", json.loads(r.content[0].text)["messages"][0]["content"])


# ================================================================ 4. code mode
class DemoSandboxProvider:
    """A stand-in so this lesson runs without extra installs.

    THIS IS NOT A SANDBOX -- it just exec()s the model's code in this
    process. The real default, MontySandboxProvider (pip install
    'fastmcp[code-mode]'), caps duration and memory. `external_functions`
    is how CodeMode injects `call_tool` into the script's scope.
    """

    async def run(
        self,
        code: str,
        *,
        inputs: dict[str, Any] | None = None,
        external_functions: dict[str, Callable[..., Any]] | None = None,
    ) -> Any:
        src = "async def __main():\n" + textwrap.indent(code, "    ")
        scope: dict[str, Any] = dict(external_functions or {}) | dict(inputs or {})
        exec(src, scope)                                     # noqa: S102 -- demo only
        return await scope["__main"]()


# The LLM writes this. call_tool() returns structuredContent, and a plain
# string return gets wrapped as {"result": ...} (lesson 06) -- hence
# a["result"]. Only the final `return` crosses back to the model; the
# intermediate greeting never enters its context window.
CHAINED_CODE = """
greeting = await call_tool("greet", {"name": "Ada"})
translated = await call_tool("translate_greeting", {
    "text": greeting["result"], "language": "fr",
})
return translated["result"]
"""


async def demo_code_mode():
    mcp = FastMCP(
        "CodeMode",
        transforms=[
            CodeMode(
                sandbox_provider=DemoSandboxProvider(),
                max_tool_calls=10,        # default 50; bounds LLM-written loops
                # discovery_tools=[ListTools(), GetSchemas()],   # 2-stage
                # discovery_tools=[],  execute_description="..."  # single-stage
            )
        ],
    )

    @mcp.tool
    def greet(name: str) -> str:
        """Greets someone by name in English."""
        return f"Hello, {name}!"

    @mcp.tool
    def translate_greeting(text: str, language: str) -> str:
        """Translates a greeting into another language."""
        return f"[{language}] {text}"

    print("\n--- Code Mode (experimental) ---")
    async with Client(mcp) as c:
        print("greet/translate are gone; exposed:", sorted(t.name for t in await c.list_tools()))

        # stage 1: brief -- names + one-line descriptions
        r = await c.call_tool("search", {"query": "greeting translation"})
        print("\nsearch('greeting translation') ->")
        print("   ", r.content[0].text.replace("\n", "\n    "))

        # stage 2: detailed -- enough to write the call
        r = await c.call_tool("get_schema", {"tools": ["greet"]})
        print("get_schema(['greet'])          ->")
        print("   ", r.content[0].text.strip().replace("\n", "\n    ")[:200])

        # stage 3: one script, two tool calls, one value back
        r = await c.call_tool("execute", {"code": CHAINED_CODE})
        print("\nexecute(chained code)          ->", r.content[0].text)

    print(
        "\n  Fewer discovery stages = fewer round-trips but more wasted schema\n"
        "  tokens; staged discovery tends to win on large, complex servers.\n"
    )


async def main():
    await demo_regex()
    await demo_bm25()
    await demo_as_tools()
    await demo_code_mode()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Drop always_visible from demo_regex. help_ disappears from the listing
#    and must be found via search_tools first.
# 2. Call call_tool(name="call_tool") -- rejected, rather than recursing.
# 3. Give search_tools a malformed regex like "[". Regex search returns an
#    empty list instead of raising.
# 4. Swap the order in demo_bm25 so search is added BEFORE Visibility. The
#    admin tool now shows up in results -- ordering is the whole guarantee.
# 5. Write CHAINED_CODE with a loop of 20 call_tool() calls. max_tool_calls=10
#    stops it -- that cap is why a model-written loop can't melt your backend.
# 6. Drop ["result"] and pass the raw dict to translate_greeting. Read the
#    validation error: call_tool returns structuredContent, not a bare value.
# 7. Install the real sandbox (uv add 'fastmcp[code-mode]'), delete
#    sandbox_provider=..., and confirm CodeMode() uses Monty by default.
