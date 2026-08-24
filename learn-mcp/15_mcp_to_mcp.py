"""Lesson 15 -- MCP-to-MCP: One Skill Calling Another Over HTTP
================================================================

WHY THIS MATTERS:
  Production skills (story-drafting, text-archive, urgent-drafting) are
  independent services. When one skill needs another's capability — like
  story-drafting asking a quote-checker to verify quotes — it calls that
  skill via MCP over HTTP. No shared imports, no coupling. The caller uses
  the same Client + StreamableHttpTransport from lesson 05, but *inside*
  a tool handler instead of a standalone script.

  This is a NEW pattern. Today, only the backend orchestrator calls skills.
  MCP-to-MCP enables skill-to-skill communication over the same shared ALB
  that already routes backend → skill traffic.

WHAT YOU'LL LEARN:
  1. Running two HTTP MCP servers simultaneously (multi-process)
  2. One tool calling another server's tool via MCP over HTTP
  3. The one-shot client pattern *inside* a tool handler
  4. Non-fatal error handling when the downstream skill is unavailable
  5. Result parsing: extracting text from content blocks

Concepts:
  - MCP-to-MCP: skill A's tool calling skill B's tool over HTTP
  - One-shot client (inside tool): connect -> call -> disconnect per request
  - asyncio.wait_for: timeout wrapper for cross-skill calls
  - Non-fatal try/except: downstream failure doesn't break the caller's response
  - Content block parsing: call_tool() returns CallToolResult; iterate .content

Flow:
  +----------+          +-----------------+          +-------------------+
  | External |  HTTP    | Server A        |  HTTP    | Server B          |
  | Client   | ------> | (story-server)  | -------> | (quote-checker)   |
  | (main)   |  call    |                 |  MCP-to  |                   |
  |          |  tool:   | generate_story  |  -MCP    | check_quotes      |
  |          |  generate|   1. make story |  call    |   compare draft   |
  |          |  _story  |   2. call B ----+--------->|   vs source       |
  |          |          |   3. combine    |<---------+   return JSON     |
  |          |<---------|   4. return     |  result  |                   |
  +----------+          +-----------------+          +-------------------+

  In production, the shared ALB routes by path prefix:
    /story-drafting/*   -> story-drafting ECS service
    /quote-fidelity/*   -> quote-fidelity ECS service

  Maps to:
    shared/mcp_client.py (planned)           -> reusable one-shot MCP client
    generate_spot_story.py (lines 242-262)   -> calls quote-fidelity via MCP
    story-drafting/infra/config.py           -> QUOTE_FIDELITY_MCP_URL env var

PREREQUISITES: Lesson 05 (HTTP transport), Lesson 06 (client patterns)

Run:  uv run python 15_mcp_to_mcp.py

EXPECTED OUTPUT:
  Starting quote-checker server on port 8011...
  Starting story server on port 8010...
  Both servers are ready.

  ============================================================
  DEMO 1: Happy path -- story-server chains to quote-checker
  ============================================================

  Calling generate_story on story-server...

    Story: "The CEO said 'Revenue rose 15%' in the annual report."
    Quote check:
      verified: 1
        - 'Revenue rose 15%' -> VERIFIED (exact match in source)
      flagged: 0

  ============================================================
  DEMO 2: Non-fatal -- quote-checker is down, story still works
  ============================================================

  Stopping quote-checker server...
  Calling generate_story on story-server...

    Story: "The CEO said 'Revenue rose 15%' in the annual report."
    Quote check: skipped (quote-checker unavailable)

    The story was still generated -- the quote check is non-fatal.

  ============================================================
  DEMO 3: Discovery -- list tools on both servers
  ============================================================

  story-server tools:
    - generate_story: Generate a story and verify its quotes via MCP-to-MCP.
  quote-checker tools:
    - check_quotes: Check if quotes in a draft match the source text.
"""

import asyncio
import json
import multiprocessing
import time

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport

# ============================================================================
# PORTS AND URLs
# ============================================================================

STORY_PORT = 8010
QUOTE_CHECKER_PORT = 8011
STORY_URL = f"http://localhost:{STORY_PORT}"
QUOTE_CHECKER_URL = f"http://localhost:{QUOTE_CHECKER_PORT}/mcp"


# ============================================================================
# SERVER B -- Quote checker (independent skill, knows nothing about Server A)
# ============================================================================

quote_checker = FastMCP(name="quote-checker-server")


@quote_checker.custom_route("/health", methods=["GET"])
async def quote_checker_health(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok", "server": "quote-checker"})


@quote_checker.tool
async def check_quotes(draft: str, source: str) -> str:
    """Check if quotes in a draft match the source text.

    Returns JSON with verified and flagged quote comparisons.
    """
    # Simple quote extraction: find text between single quotes
    import re

    draft_quotes = re.findall(r"'([^']+)'", draft)
    source_lower = source.lower()

    verified = []
    flagged = []

    for quote in draft_quotes:
        if quote.lower() in source_lower:
            verified.append({
                "quote": quote,
                "status": "verified",
                "reason": "exact match in source",
            })
        else:
            flagged.append({
                "quote": quote,
                "status": "not_found",
                "reason": "not found in source text",
            })

    return json.dumps({
        "verified_count": len(verified),
        "flagged_count": len(flagged),
        "verified": verified,
        "flagged": flagged,
    })


def run_quote_checker():
    quote_checker.run(
        transport="http",
        host="0.0.0.0",
        port=QUOTE_CHECKER_PORT,
        json_response=True,
        stateless_http=True,
    )


# ============================================================================
# SERVER A -- Story server (calls Server B via MCP-to-MCP)
# ============================================================================

story_server = FastMCP(name="story-server")


@story_server.custom_route("/health", methods=["GET"])
async def story_health(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok", "server": "story-server"})


# -- The cross-skill client helper ------------------------------------------
# This is the same pattern that will become shared/mcp_client.py in production.
# One-shot: connect -> call -> disconnect. No connection reuse.

async def call_quote_checker_mcp(draft: str, source: str) -> dict:
    """Call quote-checker skill via MCP over HTTP (one-shot pattern).

    Mirrors the production pattern:
        transport = StreamableHttpTransport(url=os.environ["QUOTE_FIDELITY_MCP_URL"])
        async with Client(transport) as client:
            result = await client.call_tool("check_quote_fidelity", {...})
    """
    transport = StreamableHttpTransport(url=QUOTE_CHECKER_URL)
    async with Client(transport=transport) as client:
        result = await asyncio.wait_for(
            client.call_tool("check_quotes", {"draft": draft, "source": source}),
            timeout=10.0,
        )
        # call_tool() returns a CallToolResult object.
        # Iterate .content to get the list of content blocks.
        for block in result.content:
            if hasattr(block, "text"):
                return json.loads(block.text)
        return {}


@story_server.tool
async def generate_story(source_text: str) -> str:
    """Generate a story and verify its quotes via MCP-to-MCP.

    Steps:
      1. Generate a draft story (simulated -- no LLM in this lesson)
      2. Call quote-checker skill via MCP-to-MCP (non-fatal)
      3. Return combined result (story + quote check)
    """
    # Step 1: Generate story (simulated)
    draft = f"The CEO said 'Revenue rose 15%' in the annual report."
    if "profits" in source_text.lower():
        draft = f"The company reported 'Profits doubled' according to the filing."

    # Step 2: Call quote-checker via MCP (cross-skill call)
    # Wrapped in try/except -- downstream failure is non-fatal.
    # This mirrors generate_spot_story.py lines 242-262:
    #   try:
    #       result_json = await call_mcp_tool(mcp_url, "check_quote_fidelity", {...})
    #       quote_check = QuoteCheckPayload.model_validate(json.loads(result_json))
    #   except Exception as qe:
    #       logger.warning("Quote fidelity check failed (non-fatal): %s", qe)
    quote_check = None
    try:
        quote_check = await call_quote_checker_mcp(draft, source_text)
    except Exception as e:
        quote_check = {"error": str(e), "skipped": True}

    # Step 3: Return combined result
    return json.dumps({
        "story": draft,
        "quote_check": quote_check,
    })


def run_story_server():
    story_server.run(
        transport="http",
        host="0.0.0.0",
        port=STORY_PORT,
        json_response=True,
        stateless_http=True,
    )


# ============================================================================
# CLIENT -- External caller (simulates the backend orchestrator)
# ============================================================================

async def demo_happy_path():
    """Demo 1: Both servers up -- quote check runs end-to-end."""
    print("=" * 60)
    print("DEMO 1: Happy path -- story-server chains to quote-checker")
    print("=" * 60)
    print()
    print("Calling generate_story on story-server...")
    print()

    transport = StreamableHttpTransport(url=f"{STORY_URL}/mcp")
    async with Client(transport=transport) as client:
        result = await client.call_tool(
            "generate_story",
            {"source_text": "Annual report: Revenue rose 15% year over year."},
        )

        for block in result.content:
            if hasattr(block, "text"):
                data = json.loads(block.text)
                print(f'    Story: "{data["story"]}"')
                qc = data["quote_check"]
                print(f"    Quote check:")
                print(f"      verified: {qc['verified_count']}")
                for v in qc.get("verified", []):
                    print(f"        - '{v['quote']}' -> VERIFIED ({v['reason']})")
                print(f"      flagged: {qc['flagged_count']}")
                for f in qc.get("flagged", []):
                    print(f"        - '{f['quote']}' -> FLAGGED ({f['reason']})")
    print()


async def demo_error_resilience(quote_checker_proc):
    """Demo 2: Quote-checker is down -- story still generates."""
    print("=" * 60)
    print("DEMO 2: Non-fatal -- quote-checker is down, story still works")
    print("=" * 60)
    print()

    # Stop quote-checker
    print("Stopping quote-checker server...")
    quote_checker_proc.terminate()
    quote_checker_proc.join(timeout=3)

    print("Calling generate_story on story-server...")
    print()

    transport = StreamableHttpTransport(url=f"{STORY_URL}/mcp")
    async with Client(transport=transport) as client:
        result = await client.call_tool(
            "generate_story",
            {"source_text": "Annual report: Revenue rose 15% year over year."},
        )

        for block in result.content:
            if hasattr(block, "text"):
                data = json.loads(block.text)
                print(f'    Story: "{data["story"]}"')
                qc = data["quote_check"]
                if qc.get("skipped"):
                    print(f"    Quote check: skipped (quote-checker unavailable)")
                else:
                    print(f"    Quote check: {qc}")

    print()
    print("    The story was still generated -- the quote check is non-fatal.")
    print()


async def demo_discovery():
    """Demo 3: List tools on both servers."""
    print("=" * 60)
    print("DEMO 3: Discovery -- list tools on both servers")
    print("=" * 60)
    print()

    # Story server
    transport_a = StreamableHttpTransport(url=f"{STORY_URL}/mcp")
    async with Client(transport=transport_a) as client:
        tools = await client.list_tools()
        print("  story-server tools:")
        for t in tools:
            desc = (t.description or "").split("\n")[0]
            print(f"    - {t.name}: {desc}")

    # Quote checker
    transport_b = StreamableHttpTransport(url=QUOTE_CHECKER_URL)
    async with Client(transport=transport_b) as client:
        tools = await client.list_tools()
        print("  quote-checker tools:")
        for t in tools:
            desc = (t.description or "").split("\n")[0]
            print(f"    - {t.name}: {desc}")

    print()


# ============================================================================
# MAIN -- spawn both servers, run demos, clean up
# ============================================================================

def wait_for_server(url, name, max_attempts=30):
    """Poll health endpoint until server is ready."""
    import urllib.request
    for _ in range(max_attempts):
        try:
            urllib.request.urlopen(f"{url}/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    print(f"{name} failed to start!")
    return False


if __name__ == "__main__":
    # Spawn Server B (quote-checker) first -- Server A depends on it
    qc_proc = multiprocessing.Process(target=run_quote_checker, daemon=True)
    qc_proc.start()
    print(f"Starting quote-checker server on port {QUOTE_CHECKER_PORT}...")

    # Spawn Server A (story-server)
    story_proc = multiprocessing.Process(target=run_story_server, daemon=True)
    story_proc.start()
    print(f"Starting story server on port {STORY_PORT}...")

    # Wait for both to be ready
    if not wait_for_server(f"http://localhost:{QUOTE_CHECKER_PORT}", "quote-checker"):
        qc_proc.terminate()
        story_proc.terminate()
        raise SystemExit(1)

    if not wait_for_server(STORY_URL, "story-server"):
        qc_proc.terminate()
        story_proc.terminate()
        raise SystemExit(1)

    print("Both servers are ready.\n")

    try:
        # Demo 1: Happy path (both servers up)
        asyncio.run(demo_happy_path())

        # Demo 2: Error resilience (quote-checker goes down)
        asyncio.run(demo_error_resilience(qc_proc))

        # Restart quote-checker for Demo 3
        qc_proc = multiprocessing.Process(target=run_quote_checker, daemon=True)
        qc_proc.start()
        wait_for_server(f"http://localhost:{QUOTE_CHECKER_PORT}", "quote-checker")

        # Demo 3: Discovery
        asyncio.run(demo_discovery())
    finally:
        qc_proc.terminate()
        qc_proc.join(timeout=3)
        story_proc.terminate()
        story_proc.join(timeout=3)
        print("Both servers stopped.")

    # -- Key takeaway --------------------------------------------------------
    # MCP-to-MCP is just the one-shot client pattern from lesson 06, used
    # *inside* a tool handler instead of a standalone script:
    #
    #   async def call_other_skill(args):
    #       transport = StreamableHttpTransport(url=OTHER_SKILL_MCP_URL)
    #       async with Client(transport=transport) as client:
    #           result = await asyncio.wait_for(
    #               client.call_tool("tool_name", args), timeout=10.0
    #           )
    #           for block in result.content:
    #               if hasattr(block, "text"):
    #                   return json.loads(block.text)
    #
    # Production pattern (story-drafting -> quote-fidelity):
    #   1. URL comes from env var: QUOTE_FIDELITY_MCP_URL
    #   2. Feature-flagged: only runs in dev/qa
    #   3. Non-fatal: try/except so the draft still returns if checker is down
    #   4. Shared utility: shared/mcp_client.py wraps this for any skill
    #
    # This keeps skills fully decoupled: story-drafting never imports
    # quote-fidelity code. They communicate only through MCP over HTTP.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a third server ("fact-checker") and have story-server call
    #    both quote-checker AND fact-checker in parallel with asyncio.gather()
    # 2. Add retry with exponential backoff to call_quote_checker_mcp()
    #    (reuse the pattern from lesson 06's call_with_retry)
    # 3. Forward the quote-check result as a _meta.forwarded_blocks entry
    #    instead of inlining it (combine lesson 08 + this lesson)
    # 4. Replace the hardcoded QUOTE_CHECKER_URL with os.environ.get()
    #    and test with/without the env var set
