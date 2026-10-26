"""Background tasks -- not waiting for a slow tool  (intermediate)
=======================================================================

If the server marks a tool backgroundable (@mcp.tool(task=True)), you can call it two ways:

    call_tool(...)                   EASY: looks like any call; the client polls
                                     for you and returns the final result. Default.
    call_tool_task(client, ...)      EXPLICIT: returns a ToolTask handle right away
                                     so you can do other work meanwhile.
        task.status()                what's happening now
        task.result()                wait for and return the result
        task.cancel()                ask it to stop (cooperative -- it may finish first)

    client                       server
    call_tool_task ────────────► starts the job, replies at once with a task id
    task.status()  ────────────► "working"
    task.status()  ────────────► "completed"
    task.result()  ────────────► the result

SETUP  needs `fastmcp[tasks]`; importing fastmcp_tasks turns it on for every Client.
       Modern protocol only: with Client(mode="legacy") the tool just runs normally.

Level: ADVANCED   (server side: ../server/advanced/11_tasks_versioning_extensions.py)
Run:  uv run python advanced/06_tasks.py
"""

import asyncio

from fastmcp import Client
from fastmcp_tasks import call_tool_task      # importing this enables task support
from greet_server import mcp


async def main():
    async with Client(mcp) as client:
        # 1. the easy way -- nothing looks different
        r = await client.call_tool("greet_in_background", {"names": ["Ada", "Bob"]})
        print("call_tool      ->", r.data)

        # 2. the explicit way -- a handle you poll
        task = await call_tool_task(client, "greet_in_background", {"names": ["Cleo"]})
        print("task started   ->", task.task_id)
        while (status := await task.status()).status not in ("completed", "failed", "cancelled"):
            print("  still", status.status, "...")
            await asyncio.sleep(0.1)
        print("call_tool_task ->", (await task.result()).data)

        # 3. cancelling
        task = await call_tool_task(client, "greet_in_background", {"names": ["Dee"]})
        await task.cancel()
        print("after cancel   ->", (await task.status()).status)


if __name__ == "__main__":
    asyncio.run(main())
