"""Lesson 02 -- Tools are SCHEMAS, not functions
====================================================

The model in lesson 01 never saw Python code. A real model never does
either: it's handed a catalog of tool SCHEMAS -- name, description,
parameters -- and picks one by name with arguments matching that schema.
YOUR code is what maps "the model said call 'greet' with {'name': 'Ada'}"
back to the real Python function and actually runs it.

This is the exact same idea as an MCP tool's `inputSchema`
(learn-fastmcp-server lesson 06) -- FastMCP builds that schema from your
function's signature and docstring automatically. This lesson builds the
same kind of schema by hand, from the same two sources, so you can see
where it comes from:

    def greet(name: str) -> str:        signature   -> schema["parameters"]
        '''Greets someone by name.'''   docstring   -> schema["description"]

    {
        "name": "greet",
        "description": "Greets someone by name.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }
    }

    your function  --describe_tool()-->  schema  --[sent to the model]-->
    model picks "greet" + {"name": "Ada"}  --[comes back as a decision]-->
    your code looks up TOOLS["greet"], VALIDATES the arguments against the
    schema, then calls TOOLS["greet"](name="Ada")

Run:  uv run python 02_tools_and_function_calling.py
"""

import inspect
from typing import Callable

from tools import TOOLS, greet, lookup_weather, translate

PY_TO_JSON_TYPE = {str: "string", int: "integer", float: "number", bool: "boolean"}


def describe_tool(fn: Callable) -> dict:
    """Builds a model-facing schema from a real function -- the same two
    inputs FastMCP's @mcp.tool decorator reads: the signature and the
    docstring."""
    sig = inspect.signature(fn)
    properties, required = {}, []
    for name, param in sig.parameters.items():
        properties[name] = {"type": PY_TO_JSON_TYPE.get(param.annotation, "string")}
        if param.default is inspect.Parameter.empty:
            required.append(name)
    return {
        "name": fn.__name__,
        "description": (fn.__doc__ or "").strip(),
        "parameters": {"type": "object", "properties": properties, "required": required},
    }


def validate_arguments(schema: dict, arguments: dict) -> None:
    """What your code must do before calling anything -- the model's output
    is still just text/structured data, not a trusted function call."""
    missing = [p for p in schema["parameters"]["required"] if p not in arguments]
    if missing:
        raise ValueError(f"{schema['name']}: missing required argument(s) {missing}")


TOOL_SCHEMAS = {name: describe_tool(fn) for name, fn in TOOLS.items()}


def call_tool(name: str, arguments: dict):
    """The full round trip: schema lookup, validation, THEN the real call."""
    schema = TOOL_SCHEMAS[name]
    validate_arguments(schema, arguments)
    return TOOLS[name](**arguments)


if __name__ == "__main__":
    print("--- the catalog a model would be given ---")
    for name, schema in TOOL_SCHEMAS.items():
        print(f"  {name}{tuple(schema['parameters']['properties'])} -- {schema['description']}")

    print("\n--- a valid call ---")
    print("call_tool('greet', {'name': 'Ada'}) ->", call_tool("greet", {"name": "Ada"}))

    print("\n--- an invalid call -- missing a required argument ---")
    try:
        call_tool("translate", {"text": "Hello, Ada!"})   # missing 'language'
    except ValueError as e:
        print("rejected before the function ever ran ->", e)

# Expected output:
#
# --- the catalog a model would be given ---
#   greet('name',) -- Greets someone by name, in English.
#   translate('text', 'language') -- Translates text into another language (simulated).
#   lookup_weather('city',) -- Looks up the weather for a city (simulated, deterministic).
#
# --- a valid call ---
# call_tool('greet', {'name': 'Ada'}) -> Hello, Ada!
#
# --- an invalid call -- missing a required argument ---
# rejected before the function ever ran -> translate: missing required argument(s) ['language']
