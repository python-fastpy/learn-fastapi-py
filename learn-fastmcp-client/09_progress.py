"""Lesson 09 -- Progress: watching a slow tool as it runs
============================================================

Long tool calls can report how far along they are. You supply a
`progress_handler`; the client calls it every time the server sends an update.

    async def progress_handler(progress: float, total: float | None, message: str | None):
        ...

    Client(mcp, progress_handler=progress_handler)     # every call
    client.call_tool(..., progress_handler=other_fn)   # just this one call

`total` may be None (an indeterminate job -- just count upward). Nothing
requires progress to reach `total`; the server decides when the call is done.

Run:  uv run python 09_progress.py
"""

import asyncio

from fastmcp import Client
from target_server import mcp


async def progress_handler(progress: float, total: float | None, message: str | None) -> None:
    if total is not None:
        pct = (progress / total) * 100
        print(f"  {pct:5.1f}%  {message or ''}")
    else:
        print(f"  {progress:g}  {message or ''}")


async def main():
    async with Client(mcp, progress_handler=progress_handler) as client:
        result = await client.call_tool("greet_slowly", {"names": ["Ada", "Bob", "Cleo"]})
        print("\ngreet_slowly ->", result.data)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Pass a DIFFERENT progress_handler just to this one call_tool() --
#    it overrides the client-level one for that call only.
# 2. Call a tool that never reports progress at all -- your handler simply
#    never runs. Nothing errors.
# 3. Have your handler render a real progress bar (\r + fixed width) instead
#    of printing a new line each time.
