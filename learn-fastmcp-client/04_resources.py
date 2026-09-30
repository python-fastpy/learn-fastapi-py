"""Lesson 04 -- Reading resources from a client
================================================

A resource is read-only data addressed by URI, not called by name like a
tool. Discover them, then read one:

    list_resources()             fixed resources
    list_resource_templates()    resources whose URI has a {parameter}
    read_resource(uri)           fetch one, by URI

For a template, just fill the placeholder directly into the URI string you
pass to read_resource() -- there's no separate "call with arguments" step.

read_resource() always returns a LIST of content items (a single resource
can hand back more than one representation). Each item is one of:

    TextResourceContents   -> item.text        (plus item.mime_type)
    BlobResourceContents   -> item.blob         (base64-encoded binary)

Run:  uv run python 04_resources.py
"""

import asyncio

from fastmcp import Client
from target_server import mcp


async def main():
    async with Client(mcp) as client:
        # 1. discover
        print("resources:", [str(r.uri) for r in await client.list_resources()])
        print("templates:", [t.uri_template for t in await client.list_resource_templates()])

        # 2. read a fixed resource
        content = await client.read_resource("data://greeting")
        print("\ndata://greeting ->", content[0].text)
        print("  mime_type       :", content[0].mime_type)

        # 3. read a template -- the parameter goes straight into the URI
        content = await client.read_resource("greet://Ada")
        print("\ngreet://Ada     ->", content[0].text)

        # 4. the raw protocol result, no convenience unwrapping
        raw = await client.read_resource_mcp("data://greeting")
        print("\nread_resource_mcp ->", type(raw).__name__)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Read greet://Bob and greet://Ada in the same script -- one template
#    function, two different URIs.
# 2. Read a URI that doesn't exist and see what error you get.
# 3. Write a resource of your own that returns bytes, then decode
#    content[0].blob with base64.b64decode() on the client side.
