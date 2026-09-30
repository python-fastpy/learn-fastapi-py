"""Lesson 08 -- Background tasks: not waiting for a slow tool
================================================================

Some tools take too long to just sit and wait for. If the server marks a
tool as backgroundable, you have two ways to call it:

    call_tool(...)          the EASY way -- looks exactly like any other
                             call; the client polls behind the scenes and
                             hands you the final result. Use this by default.

    call_tool_task(...)     the EXPLICIT way -- returns a ToolTask handle
                             immediately, so you can do other work, check
                             on it, or cancel it.

    task.status()           what's happening right now
    task.result()           wait for it to finish and return the result
    task.cancel()            ask it to stop (cooperative -- it may finish first)

Setup: `import fastmcp_tasks` once, anywhere, turns this on for every
Client in the process (needs `pip install fastmcp[tasks]`). It also needs
the modern protocol -- `mode="legacy"` never uses background tasks; the
tool just runs synchronously there instead.

Run:  uv run python 08_tasks.py
"""

import asyncio

from fastmcp import Client
from fastmcp_tasks import call_tool_task  # importing this enables task support
from target_server import mcp


# ------------------------------------------------------- 1. the easy way
async def demo_transparent():
    async with Client(mcp, mode="auto") as client:
        # looks like a normal call -- the client polls for you underneath
        result = await client.call_tool("greet_in_background", {"names": ["Ada", "Bob"]})
        print("call_tool (transparent) ->", result.data)


# --------------------------------------------------- 2. the explicit way
async def demo_explicit():
    async with Client(mcp, mode="auto") as client:
        task = await call_tool_task(client, "greet_in_background", {"names": ["Cleo"]})
        print(f"\ntask started: {task.task_id}")

        while True:
            status = await task.status()
            if status.status in ("completed", "failed", "cancelled"):
                break
            print(f"  still {status.status} ...")
            await asyncio.sleep(0.1)

        result = await task.result()
        print("call_tool_task (explicit) ->", result.data)


async def main():
    await demo_transparent()
    await demo_explicit()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Call greet_in_background via call_tool_task, then task.cancel() it
#    immediately -- read the final status.
# 2. Try demo_explicit with Client(mcp, mode="legacy") -- the tool now
#    just runs synchronously; there's no task to poll.
# 3. If a background task pauses to ask a question (lesson 07's pattern),
#    pass an elicitation_handler to Client() so task.result() can answer
#    it automatically instead of raising.
