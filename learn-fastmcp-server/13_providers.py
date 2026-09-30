"""Lesson 13 -- Providers: where components come from
====================================================

A provider is a SOURCE of tools, resources and prompts. Every server has at
least one. Providers are queried AT REQUEST TIME, so what they return can
change without restarting the server. Every provider below supplies the
same thing: a way to greet someone.

    LocalProvider        your @mcp.tool decorators -- always checked first
    FastMCPProvider      another FastMCP server, via mcp.mount()
    ProxyProvider         a remote MCP server, via create_proxy()
    FileSystemProvider   .py files discovered on disk
    SkillsProvider       SKILL.md folders exposed as resources
    your own              subclass Provider and implement _list_tools

PROVIDER vs MIDDLEWARE: a provider decides what EXISTS; middleware and
visibility decide what a given request is allowed to SEE. Let the provider
expose everything, then narrow per request.

Run:  uv run python 13_providers.py
"""

import asyncio
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from pathlib import Path

from fastmcp import Client, FastMCP
from fastmcp.resources import Resource
from fastmcp.server import create_proxy
from fastmcp.server.providers import (
    FileSystemProvider,
    LocalProvider,
    Provider,
)
from fastmcp.server.providers.skills import SkillsDirectoryProvider
from fastmcp.tools import Tool

HERE = Path(__file__).parent
COMPONENTS = HERE / "_components"
SKILLS = HERE / "_skills"


# ============================================= 1. LocalProvider, standalone
async def demo_local():
    """A LocalProvider can live on its own and be shared by many servers."""
    shared = LocalProvider()

    @shared.tool
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    @shared.resource("data://greeting-config")
    def config() -> str:
        return '{"language": "en"}'

    server1 = FastMCP("Server1", providers=[shared])
    server2 = FastMCP("Server2", providers=[shared])

    @server2.tool
    def greet_debug(name: str) -> str:
        """Local to server2 only."""
        return f"[debug] {name}"

    async with Client(server1) as c:
        print("server1 (shared only)      :", sorted(t.name for t in await c.list_tools()))
    async with Client(server2) as c:
        print("server2 (shared + local)   :", sorted(t.name for t in await c.list_tools()))

    # Every server also has mcp.local_provider -- that is where decorators land,
    # and where removal lives.
    server2.local_provider.remove_tool("greet_debug")
    async with Client(server2) as c:
        print("after remove_tool          :", sorted(t.name for t in await c.list_tools()))


# ============================================== 2. FileSystemProvider
def write_component_files() -> None:
    """Components as plain files -- no imports in either direction.

    Normally either your tool modules import the server, or the server imports
    every tool module. The filesystem provider breaks that cycle: these files
    use the STANDALONE decorators, so they never mention a server.
    """
    (COMPONENTS / "tools").mkdir(parents=True, exist_ok=True)
    (COMPONENTS / "resources").mkdir(parents=True, exist_ok=True)

    (COMPONENTS / "tools" / "greeting.py").write_text(
        'from fastmcp.tools import tool\n'
        '\n'
        '\n'
        '@tool\n'
        'def greet(name: str) -> str:\n'
        '    """Greets someone by name."""\n'
        '    return f"Hello, {name}!"\n'
        '\n'
        '\n'
        '@tool(name="greet-formally", tags={"formal"})\n'
        'def greet_formal(name: str, title: str = "Dr.") -> str:\n'
        '    """Greets someone with their title."""\n'
        '    return f"Good day, {title} {name}."\n'
        '\n'
        '\n'
        'def _helper() -> str:\n'
        '    """Leading underscore -> skipped even if decorated."""\n'
        '    return "hidden"\n',
        encoding="utf-8",
    )
    (COMPONENTS / "resources" / "config.py").write_text(
        'from fastmcp.resources import resource\n'
        '\n'
        '\n'
        '@resource("data://greeting-config")\n'
        'def get_greeting_config() -> str:\n'
        '    """The greeting templates this server knows."""\n'
        '    return \'{"en": "Hello, {name}!"}\'\n',
        encoding="utf-8",
    )
    # An unimportable file only warns -- the server still starts.
    (COMPONENTS / "broken.py").write_text("import a_module_that_does_not_exist\n", encoding="utf-8")


async def demo_filesystem():
    write_component_files()

    # Anchor on __file__, not the cwd. reload=True re-scans EVERY request:
    # development only, it costs on each call.
    provider = FileSystemProvider(root=COMPONENTS, reload=True)
    mcp = FastMCP("FilesystemDemo", providers=[provider])

    async with Client(mcp) as c:
        print("\ndiscovered from disk       :", sorted(t.name for t in await c.list_tools()))
        print("  resources                :", [str(r.uri) for r in await c.list_resources()])
        r = await c.call_tool("greet-formally", {"name": "Lovelace"})
        print("  greet-formally           ->", r.data)

    # reload=True picks up a new file with no restart
    (COMPONENTS / "tools" / "late.py").write_text(
        'from fastmcp.tools import tool\n'
        '\n'
        '\n'
        '@tool\n'
        'def greet_casually(name: str) -> str:\n'
        '    """Written after the server started."""\n'
        '    return f"Hey, {name}!"\n',
        encoding="utf-8",
    )
    async with Client(mcp) as c:
        print("  after writing a new file :", sorted(t.name for t in await c.list_tools()))

    # Directory layout is purely organisational -- every .py is found
    # recursively. __init__.py and __pycache__ are skipped; add an
    # __init__.py to make relative imports inside your components work.


# ==================================================== 3. a custom provider
class DictProvider(Provider):
    """The smallest useful provider: a dict of callables."""

    def __init__(self, tools: dict[str, Callable]):
        super().__init__()                 # every custom provider must do this
        self._tools = [Tool.from_function(fn, name=name) for name, fn in tools.items()]

    async def _list_tools(self) -> Sequence[Tool]:
        return self._tools


class ApiGreetingProvider(Provider):
    """Greeting resources sourced from an 'API', with lifespan-managed setup.

    Worth copying: the client is built once in lifespan() and shared (not
    rebuilt per request), and each Resource fetches its content lazily,
    only when actually read.
    """

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.client = None

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        self.client = {"connected_to": self.base_url}     # stand-in for httpx
        print(f"  [provider lifespan] opened {self.base_url}")
        try:
            yield
        finally:
            print("  [provider lifespan] closed")
            self.client = None

    async def _list_resources(self) -> Sequence[Resource]:
        # A real provider would GET /greetings here, on every listing.
        items = [{"lang": "en", "hello": "Hello"}, {"lang": "fr", "hello": "Bonjour"}]
        return [self._make(i) for i in items]

    def _make(self, data: dict) -> Resource:
        lang, hello = data["lang"], data["hello"]

        async def read_content() -> str:
            return f"{hello}, {{name}}!  (from {self.client['connected_to']})"

        return Resource.from_function(
            read_content,
            uri=f"api://greeting/{lang}",
            name=f"greeting-{lang}",
            mime_type="text/plain",
        )


async def demo_custom():
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    def farewell(name: str) -> str:
        """Says goodbye to someone."""
        return f"Goodbye, {name}!"

    print("\ncustom providers")
    mcp = FastMCP(
        "Custom",
        providers=[
            DictProvider({"greet": greet, "farewell": farewell}),
            ApiGreetingProvider("https://greetings.example.com"),
        ],
    )
    # add_provider() works after construction too:
    #   mcp.add_provider(DictProvider({...}))

    async with Client(mcp) as c:
        print("  tools      :", sorted(t.name for t in await c.list_tools()))
        print("  resources  :", [str(r.uri) for r in await c.list_resources()])
        print("  read one   ->", (await c.read_resource("api://greeting/fr"))[0].text)


# ==================================================== 4. the proxy provider
async def demo_proxy():
    """create_proxy() re-exposes another MCP server through yours."""
    backend = FastMCP("Backend")

    @backend.tool
    def greet(name: str) -> str:
        """Greets someone -- lives in the backend server."""
        return f"Hello from the backend, {name}!"

    # Accepts a URL, a Path to a script, a config dict, a transport, or a
    # FastMCP instance. Proxies are LAZY: nothing is contacted until used.
    proxy = create_proxy(backend, name="GreetingProxy")

    async with Client(proxy) as c:
        print("\nproxy tools                :", sorted(t.name for t in await c.list_tools()))
        print("  through the proxy        ->", (await c.call_tool("greet", {"name": "Ada"})).data)

    # Results are relayed, not re-validated -- that's the client's job.
    # A proxied list_tools() is much slower than a local one (network round
    # trip), so ProxyProvider caches component lists for cache_ttl seconds
    # (default 300s; use cache_ttl=0 for backends that change often).
    print("  mirrored components resist edits; .copy() one to modify it locally")


# ==================================================== 5. the skills provider
def write_skill() -> None:
    (SKILLS / "greeting-etiquette").mkdir(parents=True, exist_ok=True)
    (SKILLS / "greeting-etiquette" / "SKILL.md").write_text(
        "---\n"
        "description: How to greet people appropriately across cultures\n"
        "---\n"
        "\n"
        "# Greeting Etiquette\n"
        "\n"
        "Instructions for choosing the right greeting...\n",
        encoding="utf-8",
    )
    (SKILLS / "greeting-etiquette" / "reference.md").write_text(
        "# Formality by region\n", encoding="utf-8"
    )


async def demo_skills():
    """Any folder holding a SKILL.md is a skill. They become RESOURCES."""
    write_skill()

    mcp = FastMCP("Skills Server")
    # roots can be a list; the earliest root wins on name collisions.
    # Vendor subclasses exist with fixed paths: ClaudeSkillsProvider
    # (~/.claude/skills), CursorSkillsProvider, VSCodeSkillsProvider, ...
    mcp.add_provider(SkillsDirectoryProvider(roots=SKILLS, reload=True))

    async with Client(mcp) as c:
        print("\nskill resources            :", [str(r.uri) for r in await c.list_resources()])
        main_file = await c.read_resource("skill://greeting-etiquette/SKILL.md")
        print("  SKILL.md frontmatter     ->", main_file[0].text.splitlines()[1])
        manifest = await c.read_resource("skill://greeting-etiquette/_manifest")
        print("  _manifest                ->", manifest[0].text[:100].replace("\n", " "))

    # supporting_files="template" (default) keeps listings small: only SKILL.md
    # and _manifest are listed, and clients read the manifest to find the rest.
    # supporting_files="resources" lists every file individually.
    # Path safety: "..", absolute paths, null bytes and escaping symlinks are
    # refused, so reads stay inside the skill folder.


async def main():
    await demo_local()
    await demo_filesystem()
    await demo_custom()
    await demo_proxy()
    await demo_skills()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Register DictProvider BEFORE a mounted server that has its own "greet".
#    LocalProvider is still slot 0 -- decorators win over both.
# 2. Set reload=False in demo_filesystem, write another file, and confirm it
#    is NOT picked up.
# 3. Delete _components/broken.py's bad import and watch the warning stop.
# 4. Override _get_tool on DictProvider so lookups don't scan the whole list.
# 5. Point create_proxy() at a real URL and time list_tools() against local.
