"""Lesson 15 -- MCP-to-MCP: one skill calling another over HTTP
===============================================================

Two separate services. greeting-server can say hello; only translate-server
can translate. So greet() opens its own MCP client and calls the other
skill -- no shared imports, no shared code, just HTTP.

  ┌─ YOU ──┐        ┌──── greeting-server :8010 ─────┐    ┌ translate-server :8011 ┐
  │        │  HTTP  │ greet("Shubham", "French")     │    │                        │
  │ call   │ ─────► │                                │    │ translate(text, lang)  │
  │ greet  │        │ 1. english = "Hello, Shubham!" │    │                        │
  │        │        │ 2. one-shot Client(:8011) ─────┼───►│ -> "[French] Hello,    │
  │        │        │    (a NESTED MCP call, made    │HTTP│     Shubham!"          │
  │        │        │     inside a tool handler) ◄───┼────┤                        │
  │        │ ◄───── │ 3. return both                 │    └────────────────────────┘
  └────────┘        │                                │
                    │ if :8011 is down -> except ->  │
                    │ return english anyway          │
                    └────────────────────────────────┘

  1. The nested call is the SAME one-shot client from lesson 07 (connect ->
     call -> disconnect), just used inside @mcp.tool instead of a script.
  2. asyncio.wait_for caps it -- a slow neighbour must not hang your tool.
  3. The try/except is the point: a downstream skill being down degrades the
     result (no translation) instead of failing the call.
  4. greeting-server holds no translate code. The only contract is the tool
     name and its arguments.

  In production a shared ALB routes by path prefix, so the URL is the only
  thing that changes:
    /story-drafting/*  -> story-drafting service
    /quote-fidelity/*  -> quote-fidelity service

Run:  uv run python 15_mcp_to_mcp.py      (spawns both servers, then stops them)

Maps to: generate_spot_story.py calling quote-fidelity (non-fatal),
QUOTE_FIDELITY_MCP_URL in story-drafting/infra/config.py
"""

import asyncio
import multiprocessing
import time
import urllib.request

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from starlette.responses import JSONResponse

GREET_PORT, TRANSLATE_PORT = 8010, 8011
TRANSLATE_URL = f"http://localhost:{TRANSLATE_PORT}/mcp"

# -- Skill B: translate-server (knows nothing about greeting-server) ---------

translate_server = FastMCP(name="translate-server")


@translate_server.tool
def translate(text: str, language: str) -> dict:
    """Translate text into another language (simulated)."""
    return {"translated": f"[{language}] {text}"}


@translate_server.custom_route("/health", methods=["GET"])
async def translate_health(request):
    return JSONResponse({"status": "ok"})


# -- Skill A: greeting-server (calls skill B) --------------------------------

greeting_server = FastMCP(name="greeting-server")


@greeting_server.custom_route("/health", methods=["GET"])
async def greeting_health(request):
    return JSONResponse({"status": "ok"})


async def call_translate_skill(text: str, language: str) -> str:
    """One-shot MCP call to the other skill. Becomes shared/mcp_client.py."""
    async with Client(transport=StreamableHttpTransport(url=TRANSLATE_URL)) as client:
        r = await asyncio.wait_for(
            client.call_tool("translate", {"text": text, "language": language}),
            timeout=5.0,                                   # 2. never hang on a neighbour
        )
        return r.data["translated"]


@greeting_server.tool
async def greet(name: str, language: str = "French") -> dict:
    """Greet someone, translated by the translate skill when it is reachable."""
    english = f"Hello, {name}!"                            # 1. our own work

    try:
        return {"greeting": english, "translated": await call_translate_skill(english, language)}
    except Exception as e:                                 # 3. non-fatal degradation
        return {"greeting": english, "translated": None, "note": f"translate skill down ({type(e).__name__})"}


# -- Running the two servers as separate processes ----------------------------

def _serve(server: FastMCP, port: int):
    server.run(transport="http", host="127.0.0.1", port=port,
               json_response=True, stateless_http=True, show_banner=False,
               log_level="warning")            # quiet: keep the lesson output readable


# Each process target must be a module-level function taking no arguments:
# on Windows, multiprocessing re-imports this file in the child instead of
# forking, so a FastMCP object cannot be pickled across.
def serve_translate():
    _serve(translate_server, TRANSLATE_PORT)


def serve_greeting():
    _serve(greeting_server, GREET_PORT)


def _spawn(target, port: int) -> multiprocessing.Process:
    proc = multiprocessing.Process(target=target, daemon=True)
    proc.start()
    for _ in range(40):                                     # poll /health until ready
        try:
            urllib.request.urlopen(f"http://localhost:{port}/health", timeout=1)
            return proc
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"server on :{port} never came up")


async def call_greet(label: str):
    async with Client(transport=StreamableHttpTransport(url=f"http://localhost:{GREET_PORT}/mcp")) as client:
        r = await client.call_tool("greet", {"name": "Shubham", "language": "French"})
        print(f"  {label}")
        print(f"    greeting  : {r.data['greeting']}")
        print(f"    translated: {r.data['translated']}")
        if r.data.get("note"):
            print(f"    note      : {r.data['note']}")


if __name__ == "__main__":
    translate_proc = _spawn(serve_translate, TRANSLATE_PORT)
    greeting_proc = _spawn(serve_greeting, GREET_PORT)
    print(f"translate-server :{TRANSLATE_PORT} and greeting-server :{GREET_PORT} are up\n")

    try:
        print("1. both skills up")
        asyncio.run(call_greet("greet -> chained to translate-server"))

        print("\n2. translate-server stopped -- the nested call now fails")
        translate_proc.terminate()
        translate_proc.join(timeout=3)
        asyncio.run(call_greet("greet -> still returns, minus the translation"))
        print("\n   The greeting survived. A dead neighbour degrades the result, "
              "it does not break the call.")
    finally:
        for proc in (translate_proc, greeting_proc):
            proc.terminate()
            proc.join(timeout=3)
        print("\nboth servers stopped")

# Exercises:
# 1. Read TRANSLATE_URL from os.environ so the neighbour's address is config,
#    not code (that is how production points at another skill).
# 2. Add a third skill and call it alongside translate with asyncio.gather.
# 3. Retry the nested call with exponential backoff (lesson 07) before
#    giving up on it.
# 4. Return the translation as a forwarded block instead (lesson 09).
