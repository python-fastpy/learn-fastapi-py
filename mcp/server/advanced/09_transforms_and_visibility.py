"""Transforms & visibility -- change what the client SEES, not your code
==============================================================================

    your tools ──► [transform A] ──► [transform B] ──► client
                    added first       sees A's output  -> ORDER MATTERS

RENAME & RESHAPE
    Namespace("en")           greet -> en_greet,  data://x -> data://en/x
    ToolTransform({...})      rename / redescribe a tool you don't own
    Tool.from_tool(...)       rename args, hide args (default / default_factory),
                              wrap with transform_fn + forward(); raise ToolError there
    Transform subclass        your own rule: list_tools() AND get_tool()

CHANGE THE SURFACE
    Regex/BM25SearchTransform 500 tools? list only search_tools + call_tool
                              (hidden tools are still callable directly)
    ResourcesAsTools / PromptsAsTools   for tools-only clients
    CodeMode (experimental)   the LLM writes Python chaining calls in a sandbox:
                              search -> get_schema -> execute (max_tool_calls caps loops)

VISIBILITY -- hidden = not listed AND not callable
    mcp.disable(tags={"admin"})            mcp.enable(tags={"safe"}, only=True)
    filters: names= tags= keys= components={"tool","prompt",...}   later calls win
    !! several filters in ONE call INTERSECT -- for "x OR y" use two calls
    keys look like "tool:name@version"; provider rules first, server rules win
    ctx.enable_components(...) per session (CAVEAT: in 4.1.4 in-memory, other
    clients saw it too -- verify over HTTP)
    !! a DEFAULT, not security -- use auth for things that must be unreachable
FINGERPRINT  hash tool.key + input schema, diff in CI to catch contract drift

Level: ADVANCED
Run:  uv run python advanced/09_transforms_and_visibility.py      (from mcp/server)
Test in Inspector:  uv run fastmcp dev inspector advanced/09_transforms_and_visibility.py
"""

import asyncio
import hashlib
import json
import textwrap
import uuid
from collections.abc import Sequence

from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.experimental.transforms.code_mode import CodeMode
from fastmcp.server.transforms import Namespace, PromptsAsTools, ResourcesAsTools, ToolTransform, Transform
from fastmcp.server.transforms.search import BM25SearchTransform, RegexSearchTransform
from fastmcp.tools import Tool, tool
from fastmcp.tools.tool_transform import ArgTransform, ToolTransformConfig, forward


def greeting_server() -> FastMCP:
    mcp = FastMCP("Greetings")

    @mcp.tool(tags={"safe"})
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    @mcp.tool(tags={"safe"})
    def translate_greeting(text: str, language: str) -> str:
        """Translates a greeting into another language."""
        return f"[{language}] {text}"

    @mcp.tool(tags={"admin"})
    def delete_greeting(greeting_id: str) -> bool:
        """Admin-only: deletes a saved greeting."""
        return True

    @mcp.resource("data://greeting")
    def config() -> str:
        return "Hello, {name}!"

    @mcp.prompt
    def ask_greeting(name: str) -> str:
        return f"Write a greeting for {name}."

    return mcp


async def names(mcp: FastMCP) -> list[str]:
    async with Client(mcp) as c:
        return sorted(t.name for t in await c.list_tools())


# ======================================================== 1. rename & reshape
@tool                                      # standalone: builds a Tool, registers nowhere
def raw_greet(n: str, uid: str, req: str) -> str:
    return f"Hello, {n}! (user {uid}, req {req})"


greet_as_me = Tool.from_tool(raw_greet, name="greet_as_me", transform_args={
    "n": ArgTransform(name="name", description="Who to greet."),                     # rename
    "uid": ArgTransform(hide=True, default="user-123"),                              # hide, fixed
    "req": ArgTransform(hide=True, default_factory=lambda: uuid.uuid4().hex[:6]),    # hide, fresh
})


async def must_have_name(name: str) -> str:            # wraps execution; new arg names
    if not name.strip():
        raise ToolError("name is required")
    return await forward(name=name)


greet_checked = Tool.from_tool(greet_as_me, name="greet_checked", transform_fn=must_have_name)


class HideTag(Transform):
    """A custom transform. Implement BOTH listing and lookup."""
    def __init__(self, tag: str):
        self.tag = tag

    async def list_tools(self, tools: Sequence[Tool]) -> Sequence[Tool]:
        return [t for t in tools if self.tag not in t.tags]

    async def get_tool(self, name, call_next, *, version=None):
        t = await call_next(name, version=version)          # pass version on
        return t if t and self.tag not in t.tags else None   # None = not found


def build_reshaped() -> FastMCP:
    mcp = FastMCP("Reshaped")
    mcp.mount(greeting_server(), namespace="api")                                # api_greet ...
    mcp.add_transform(ToolTransform({"api_greet": ToolTransformConfig(name="greet")}))  # after Namespace
    mcp.add_transform(HideTag("admin"))
    mcp.add_tool(greet_as_me)
    mcp.add_tool(greet_checked)
    return mcp


async def demo_reshape():
    mcp = build_reshaped()
    async with Client(mcp) as c:
        tools = {t.name: t for t in await c.list_tools()}
        print("reshaped       ->", sorted(tools))
        print("  greet_as_me args ->", list(tools["greet_as_me"].input_schema["properties"]))
        print("  greet_as_me      ->", (await c.call_tool("greet_as_me", {"name": "Ada"})).data)
        r = await c.call_tool("greet_checked", {"name": " "}, raise_on_error=False)
        print("  greet_checked    ->", r.content[0].text)


# ===================================================== 2. change the surface
class DemoSandbox:
    """NOT a sandbox -- exec() so the demo needs no install. Real: uv add 'fastmcp[code-mode]'."""
    async def run(self, code, *, inputs=None, external_functions=None):
        scope = dict(external_functions or {}) | dict(inputs or {})
        exec("async def __main():\n" + textwrap.indent(code, "    "), scope)  # noqa: S102
        return await scope["__main"]()


async def demo_surface():
    mcp = greeting_server()
    mcp.add_transform(RegexSearchTransform(always_visible=["greet"]))
    async with Client(mcp) as c:
        print("\nsearch         ->", sorted(t.name for t in await c.list_tools()))
        r = await c.call_tool("search_tools", {"pattern": "translate"})
        print("  found        ->", [t["name"] for t in json.loads(r.content[0].text)])

    mcp = greeting_server()
    mcp.add_transform(BM25SearchTransform(max_results=3))         # natural-language ranking
    async with Client(mcp) as c:
        r = await c.call_tool("search_tools", {"query": "remove a saved greeting"})
        print("  BM25         ->", [t["name"] for t in json.loads(r.content[0].text)])

    mcp = greeting_server()
    mcp.add_transform(ResourcesAsTools(mcp))
    mcp.add_transform(PromptsAsTools(mcp))
    print("as-tools       ->", [n for n in await names(mcp) if "resource" in n or "prompt" in n])

    mcp = greeting_server()
    mcp.add_transform(CodeMode(sandbox_provider=DemoSandbox(), max_tool_calls=10))
    code = ('g = await call_tool("greet", {"name": "Ada"})\n'
            'return (await call_tool("translate_greeting", {"text": g["result"], "language": "fr"}))["result"]')
    async with Client(mcp) as c:
        print("code mode      ->", sorted(t.name for t in await c.list_tools()),
              "| execute ->", (await c.call_tool("execute", {"code": code})).content[0].text)


# ================================================================ 3. visibility
async def demo_visibility():
    m = greeting_server(); m.disable(tags={"admin"})
    print("\ndisable(admin) ->", await names(m))
    m = greeting_server(); m.enable(names={"greet"}, only=True)
    print("enable(only)   ->", await names(m))
    m = greeting_server(); m.disable(names={"greet"}, tags={"admin"})          # the TRAP
    print("names+tags trap->", await names(m), "<- nothing hidden: filters intersect")
    m = greeting_server(); m.disable(tags={"admin"})
    async with Client(m) as c:
        r = await c.call_tool("delete_greeting", {"greeting_id": "1"}, raise_on_error=False)
        print("call hidden    -> is_error =", r.is_error)


async def fingerprint(server: FastMCP, name: str) -> str:
    t = await server.get_tool(name)
    schema = t.to_mcp_tool().model_dump(mode="json", by_alias=True)["inputSchema"]
    return hashlib.sha256(json.dumps({"key": t.key, "schema": schema}, sort_keys=True).encode()).hexdigest()


async def demo_fingerprint():
    v1, v2 = FastMCP("v1"), FastMCP("v2")
    v1.tool(lambda name: name, name="greet")
    v2.tool(lambda name, formal=False: name, name="greet")       # schema changed
    print("fingerprint    -> drift detected:", await fingerprint(v1, "greet") != await fingerprint(v2, "greet"))


mcp = build_reshaped()      # what `fastmcp dev inspector` shows


async def main():
    await demo_reshape()
    await demo_surface()
    await demo_visibility()
    await demo_fingerprint()


if __name__ == "__main__":
    asyncio.run(main())
