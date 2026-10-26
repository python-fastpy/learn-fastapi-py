"""Composition & providers -- combining servers, and WHERE components come from
======================================================================================

A PROVIDER is a source of components, asked at REQUEST time (changes need no restart):

    request ──► LocalProvider        your @mcp.tool -- always checked FIRST
            ├─► mount(child)         another FastMCP server
            ├─► create_proxy(...)    a REMOTE server (URL, script path, config, object)
            ├─► FileSystemProvider   .py files on disk using standalone @tool
            ├─► SkillsDirectoryProvider  SKILL.md folders -> skill:// resources
            └─► your Provider        subclass; implement _list_tools / _list_resources

    main ──mount(english, namespace="en")──► en_greet,  data://en/greeting
         ──mount(french,  namespace="fr")──► fr_greet

  - mount is a LIVE link: tools added to the child later show up in the parent
  - no namespace + same name -> the FIRST mount wins
  - custom routes (/health) are NOT namespaced
  - every parent listing asks every child; proxies add a network hop (cached cache_ttl s)
  - a provider decides what EXISTS; middleware/visibility decide what a request SEES
  - learn-mcp lesson 11 hand-rolls a ServerRegistry for health checks + caching

Level: ADVANCED
Run:  uv run python advanced/10_composition_and_providers.py      (from mcp/server)
"""

import asyncio
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from fastmcp import Client, FastMCP
from fastmcp.server import create_proxy
from fastmcp.server.providers import FileSystemProvider, Provider
from fastmcp.server.providers.skills import SkillsDirectoryProvider
from fastmcp.tools import Tool


def language_server(name: str, hello: str) -> FastMCP:
    mcp = FastMCP(name)

    @mcp.tool
    def greet(name: str) -> str:
        return f"{hello}, {name}!"

    @mcp.resource("data://greeting")
    def template() -> str:
        return f"{hello}, {{name}}!"

    return mcp


async def tools(mcp: FastMCP) -> list[str]:
    async with Client(mcp) as c:
        return sorted(t.name for t in await c.list_tools())


# ============================================================ 1. composition
async def demo_mount():
    english, french = language_server("English", "Hello"), language_server("French", "Bonjour")
    main = FastMCP("Main")
    main.mount(english, namespace="en")
    main.mount(french, namespace="fr")
    main.mount(create_proxy(language_server("Remote", "Hola")), namespace="remote")   # proxied
    async with Client(main) as c:
        print("mounted    ->", sorted(t.name for t in await c.list_tools()))
        print("resources  ->", [str(r.uri) for r in await c.list_resources()])
        print("proxy call ->", (await c.call_tool("remote_greet", {"name": "Ada"})).data)

    english.tool(lambda name: f"Bye, {name}!", name="farewell")      # added AFTER mount
    print("live link  ->", [n for n in await tools(main) if n.startswith("en_")])

    clash = FastMCP("Clash")
    clash.mount(english); clash.mount(french)                         # no namespaces
    async with Client(clash) as c:
        print("clash      -> first wins:", (await c.call_tool("greet", {"name": "Ada"})).data)

    prod = FastMCP("Prod")                                            # parent filters a child
    prod.mount(english, namespace="api")
    prod.disable(names={"api_farewell"})
    print("prod view  ->", await tools(prod))


# ============================================================== 2. providers
class DictProvider(Provider):
    """The smallest custom provider. Real ones fetch from a DB/API, can have a
    lifespan() for shared clients, and can build resources lazily."""
    def __init__(self, fns: dict[str, Callable]):
        super().__init__()                                            # required
        self._tools = [Tool.from_function(fn, name=n) for n, fn in fns.items()]

    async def _list_tools(self) -> Sequence[Tool]:
        return self._tools


async def demo_providers():
    custom = FastMCP("Custom", providers=[DictProvider({"wave": lambda name: f"*waves at {name}*"})])
    print("\ncustom     ->", await tools(custom))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "greet.py").write_text(
            "from fastmcp.tools import tool\n\n@tool\ndef greet_formally(name: str) -> str:\n"
            "    return f'Good day, {name}.'\n", encoding="utf-8")
        fs = FastMCP("FS", providers=[FileSystemProvider(root=root, reload=True)])   # reload: dev only
        print("filesystem ->", await tools(fs))
        (root / "late.py").write_text(
            "from fastmcp.tools import tool\n\n@tool\ndef greet_casually(name: str) -> str:\n"
            "    return f'Hey, {name}!'\n", encoding="utf-8")
        print("  new file ->", await tools(fs), "(no restart)")

        skill = root / "skills" / "greeting-etiquette"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\ndescription: How to greet politely\n---\n# Etiquette\n",
                                        encoding="utf-8")
        sk = FastMCP("Skills", providers=[SkillsDirectoryProvider(roots=root / "skills")])
        async with Client(sk) as c:                  # presets: ClaudeSkillsProvider (~/.claude/skills)
            print("skills     ->", [str(r.uri) for r in await c.list_resources()])


async def main():
    await demo_mount()
    await demo_providers()


if __name__ == "__main__":
    asyncio.run(main())
