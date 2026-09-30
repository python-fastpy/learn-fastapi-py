"""Lesson 12 -- Visibility and tool fingerprinting
=================================================

Visibility decides which components exist for a client. A disabled
component disappears from listings AND cannot be called. Four greeting
tools, tagged differently, are the whole cast.

FILTERS you can pass to mcp.enable() / mcp.disable():
    names={...}       by name (or URI, for resources)
    tags={...}        matches if ANY tag matches
    components={...}  restrict to {"tool","resource","template","prompt"}
    only=True         allowlist mode: everything else becomes disabled

  WARNING -- the #1 mistake here: multiple filters in ONE call INTERSECT,
  they do not combine. `disable(names={"x"}, tags={"dangerous"})` only hides
  "x" if it ALSO has the "dangerous" tag -- otherwise it silently hides
  nothing. For "hide A OR B", make two separate calls.

Precedence when rules conflict: provider-level transforms run first, then
server-level transforms (which have the final say), and later calls beat
earlier ones.

Run:  uv run python 12_visibility.py
"""

import asyncio
import hashlib
import json

from fastmcp import Client, FastMCP
from fastmcp.server.context import Context
from fastmcp.server.providers import LocalProvider
from fastmcp.server.transforms import Visibility


def build(configure=None) -> FastMCP:
    mcp = FastMCP("GreetingService")

    @mcp.tool(tags={"safe", "read"})
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    @mcp.tool(tags={"admin", "dangerous"})
    def delete_all_greetings() -> str:
        """Delete every saved greeting."""
        return "Deleted"

    @mcp.tool(tags={"admin"})
    def reset_greeting_config() -> str:
        """Reset the greeting configuration."""
        return "Reset"

    @mcp.tool
    def greet_debug(name: str) -> str:
        """Untagged debug greeting."""
        return f"[debug] {name}"

    @mcp.resource("data://greeting-secrets", tags={"internal"})
    def secrets() -> str:
        return "s3cret template"

    @mcp.prompt(tags={"internal"})
    def internal_greeting_prompt() -> str:
        return "Internal greeting instructions"

    if configure:
        configure(mcp)
    return mcp


async def surface(mcp: FastMCP, **client_kwargs) -> dict:
    async with Client(mcp, **client_kwargs) as c:
        return {
            "tools": sorted(t.name for t in await c.list_tools()),
            "resources": sorted(str(r.uri) for r in await c.list_resources()),
            "prompts": sorted(p.name for p in await c.list_prompts()),
        }


async def demo_server_level():
    print("no filter              :", (await surface(build()))["tools"])
    print("disable(tags=admin)    :", (await surface(build(lambda m: m.disable(tags={"admin"}))))["tools"])
    print("disable(names=...)     :",
          (await surface(build(lambda m: m.disable(names={"greet_debug", "data://greeting-secrets"}))))["tools"])

    # a name crosses component types unless you add components=
    both = build(lambda m: m.disable(names={"internal_greeting_prompt"}, components={"prompt"}))
    print("components={'prompt'}  :", (await surface(both))["prompts"])

    # canonical keys: "{type}:{identifier}@{version}". The @ is ALWAYS there;
    # unversioned components end with a bare @. Read them from component.key --
    # a key without @ matches nothing and only raises a UserWarning.
    keyed = build()
    tool = await keyed.get_tool("reset_greeting_config")
    print("\nkey of reset_greeting_config:", tool.key)
    keyed.disable(keys={tool.key})
    print("disable(keys=...)      :", (await surface(keyed))["tools"])

    # THE INTERSECTION TRAP
    trap = build(lambda m: m.disable(names={"greet_debug"}, tags={"dangerous"}))
    print("\nintersection trap: disable(names={greet_debug}, tags={dangerous})")
    print("  greet_debug still visible:", "greet_debug" in (await surface(trap))["tools"],
          "  <- it has no 'dangerous' tag, so nothing matched, silently")
    fixed = build()
    fixed.disable(names={"greet_debug"})     # two calls == union
    fixed.disable(tags={"dangerous"})
    print("  two separate calls      :", (await surface(fixed))["tools"])

    # allowlist mode
    allow = build(lambda m: m.enable(tags={"safe"}, only=True))
    print("\nenable(tags=safe, only=True):", (await surface(allow))["tools"],
          "(untagged tools are hidden too)")

    # broad rule + targeted exception; later calls win
    chained = build(lambda m: m.enable(tags={"admin"}, only=True).disable(names={"delete_all_greetings"}))
    print("enable(admin,only).disable(delete_all_greetings):", (await surface(chained))["tools"])

    # the transform underneath
    raw = build(lambda m: m.add_transform(Visibility(False, tags={"admin"})))
    print("Visibility(False, tags=admin):", (await surface(raw))["tools"])


async def demo_provider_vs_server():
    """Provider transforms run first; the server overrides them."""
    provider = LocalProvider()

    @provider.tool(tags={"admin"})
    def greet_as_admin(name: str) -> str:
        """Admin greeting."""
        return f"Greetings, Administrator {name}."

    @provider.tool
    def greet(name: str) -> str:
        """Regular greeting."""
        return f"Hello, {name}!"

    provider.disable(tags={"admin"})              # provider says: hide it
    mcp = FastMCP("GreetingService", providers=[provider])
    mcp.enable(names={"greet_as_admin"})          # server says: show it anyway

    print("\nprovider.disable + server.enable ->", (await surface(mcp))["tools"])


async def demo_session_scope():
    """Session rules are documented to affect one connection only.

    CAVEAT (checked against fastmcp 4.0.10): ctx.enable_components() /
    disable_components() currently have NO observable effect -- the listing
    never changes, in-memory or over HTTP. This looks like a release gap,
    not a doc error. The code below is the documented shape, kept so it
    starts working once fixed -- don't rely on it until you see
    greet_premium actually appear after the unlock call. Global rules
    (demo_server_level, above) work correctly today.
    """
    mcp = FastMCP("Session-Aware")

    @mcp.tool(tags={"premium"})
    def greet_premium(name: str) -> str:
        """An elaborate greeting, for premium users only."""
        return f"What a delight to see you, {name}!"

    @mcp.tool
    async def unlock_premium(ctx: Context) -> str:
        """Unlock premium greetings for this session."""
        await ctx.enable_components(tags={"premium"})
        return "Premium greetings unlocked"

    @mcp.tool
    async def reset_features(ctx: Context) -> str:
        """Reset to the default greeting set."""
        await ctx.reset_visibility()
        return "Features reset to defaults"

    mcp.disable(tags={"premium"})                 # globally off

    async with Client(mcp) as a, Client(mcp) as b:
        before = sorted(t.name for t in await a.list_tools())
        print("\nsession A tools:", before)
        await a.call_tool("unlock_premium")
        after = sorted(t.name for t in await a.list_tools())
        print("A after unlock :", after)
        print("B, untouched   :", sorted(t.name for t in await b.list_tools()))
        await a.call_tool("reset_features")
        print("A after reset  :", sorted(t.name for t in await a.list_tools()))

        if before == after:
            print("  ^ unchanged: session visibility is a no-op in this fastmcp"
                  " release (see this function's docstring)")


# ==================================================== tool fingerprinting
# FastMCP has no built-in "did this tool's contract change?" check, because
# which fields count as "the contract" is up to you. Pick the fields, hash
# them, and diff the hash across builds. Two useful building blocks:
#   tool.key            a stable identity: type + name + version
#   tool.to_mcp_tool()  the exact shape the client receives
async def fingerprint(server: FastMCP, tool_name: str) -> str:
    tool = await server.get_tool(tool_name)
    if tool is None:
        raise ValueError(f"Tool {tool_name!r} not found")

    dumped = tool.to_mcp_tool().model_dump(mode="json", by_alias=True, exclude_none=True)
    payload = {
        "key": tool.key,
        "inputSchema": dumped["inputSchema"],
        # add "description" to catch doc drift, "outputSchema" if consumers
        # validate responses, "annotations" if hints drive routing
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def manifest(server: FastMCP) -> dict[str, str]:
    """A fingerprint per tool -- store this per build and diff it in CI."""
    out = {}
    for tool in await server.list_tools():
        dumped = tool.to_mcp_tool().model_dump(mode="json", by_alias=True, exclude_none=True)
        payload = {"key": tool.key, "inputSchema": dumped["inputSchema"]}
        out[tool.key] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    return out


async def demo_fingerprints():
    v1 = FastMCP("GreetingService")

    @v1.tool
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    v2 = FastMCP("GreetingService")

    @v2.tool
    def greet(name: str, formal: bool = False) -> str:  # schema CHANGED
        """Greets someone by name."""
        return f"Hello, {name}!"

    a = await fingerprint(v1, "greet")
    b = await fingerprint(v2, "greet")
    print("\nfingerprints")
    print("  greet(name)              ", a[:16], "...")
    print("  greet(name, formal)      ", b[:16], "...")
    print("  schema drift detected    ", a != b)
    print("  stable across calls      ", a == await fingerprint(v1, "greet"))

    base, current = await manifest(v1), await manifest(v2)
    changed = [k for k, v in current.items() if base.get(k) != v]
    changed += [k for k in base if k not in current]
    print("  CI drift report          ", changed)


async def main():
    await demo_server_level()
    await demo_provider_vs_server()
    await demo_session_scope()
    await demo_fingerprints()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Build a key by hand and drop the trailing "@". Confirm it matches nothing
#    and only warns -- then use component.key instead.
# 2. Re-run demo_session_scope on a newer fastmcp and see whether session
#    visibility has started working. If it has, try components={"tool"} and
#    check that only the tool list_changed notification fires.
# 3. Add "description" to the fingerprint payload, then reword greet's
#    docstring. The hash now moves on documentation drift alone.
# 4. Re-read the security caveat: disable() is a DEFAULT, not a guarantee.
#    A later enable() or a session rule can bring a component back. For
#    anything that must be unreachable: don't register it, or use auth.
