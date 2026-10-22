"""The same app, now also an MCP server.

reading_list.py itself is UNCHANGED from steps 1 and 2 -- this file just
wraps its four functions with @mcp.tool. Run this as its own process and
ANY MCP client can use it: this project's assistant (step 3), the
Inspector, Claude Desktop, Claude Code itself.

Run:  uv run python reading_list_mcp_server.py --stdio

TEST THIS SERVER BY ITSELF, WITH NO LLM INVOLVED -- the MCP Inspector
-----------------------------------------------------------------------
1. Start it:
       uv run fastmcp dev inspector reading_list_mcp_server.py
   This installs/launches the Inspector (a local web UI) and connects it
   to THIS file over stdio -- same transport 03_add_mcp.py uses, just
   driven by a human clicking buttons instead of an LLM deciding.
2. Open the URL it prints (something like
   http://127.0.0.1:6274?MCP_INSPECTOR_API_TOKEN=...). It should
   auto-open in your browser too.
3. Confirm the left sidebar lists all 4 tools: add_book, list_books,
   mark_status, remove_book. If the list is empty, the connection failed
   -- check the Inspector's connection status at the top.
4. Call add_book with title="Dune", author="Frank Herbert".
   Expect: {"id": 1, "title": "Dune", "author": "Frank Herbert",
            "status": "to_read"}
5. Call list_books with no arguments. Expect: a list containing that book.
6. Call mark_status with book_id=1, status="reading".
   Expect: the same book, now "status": "reading".
7. Call remove_book with book_id=1, then list_books again.
   Expect: an empty list.

If all five calls return what's shown above, the SERVER is proven
correct independently of any AI -- useful to know before blaming the
model if 03_add_mcp.py ever does something unexpected later.

Gotcha: the Inspector launches its OWN copy of this process, with its
own empty BOOKS list. Books you add here will NOT show up if you later
run 03_add_mcp.py directly, and vice versa -- same reason two separate
terminal runs of any script here don't share state.
"""

import sys

from fastmcp import FastMCP

from reading_list import add_book, list_books, mark_status, remove_book

mcp = FastMCP(
    name="ReadingListService",
    instructions="Manage a personal reading list: add books, list them, change status, remove them.",
)

mcp.tool(add_book)
mcp.tool(list_books)
mcp.tool(mark_status)
mcp.tool(remove_book)


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        mcp.run(show_banner=False)
    else:
        print("Run with --stdio -- this file is meant to be launched by an MCP client.")
        print("To explore it by hand instead:  uv run fastmcp dev inspector reading_list_mcp_server.py")
