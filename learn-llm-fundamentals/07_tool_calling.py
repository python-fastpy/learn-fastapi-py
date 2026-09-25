"""Lesson 07 -- Tool calling (function calling), end to end
===========================================================

READ THIS RIGHT AFTER LESSON 03. It's numbered 07 only because it was
added later; it needs nothing from lessons 04-06.

WHY THIS MATTERS:
  An LLM alone can't check the weather, read your database, or cancel an
  order -- it can only produce text (lesson 01). TOOLS close that gap:
  you describe functions, the model WRITES a request to call one, your
  code runs it, and the result goes back into the context.

      you: tool definitions + question
        |
        v
      MODEL --> "call search_orders({'customer_email': 'a@b.com'})"   <- just text, parsed
        |
        v
      YOUR CODE: validate args -> permission check -> run -> result
        |
        v
      MODEL sees the result --> answers, or asks for another tool

  Every agent, MCP server and "AI that does things" is this round trip.
  The model never executes anything. Everything that matters for safety
  and reliability happens in YOUR code, between "requested" and "ran".

WHAT YOU'LL LEARN:
  1. A tool definition: name + description + JSON Schema -- generated
     automatically from a typed Python function -- then the COMPLETE
     definition: name/description, input/output schema, error handling,
     usage examples
  2. The exact message JSON of a round trip (OpenAI and Anthropic shapes)
  3. Validating arguments, and returning errors so the model self-corrects
  4. tool_choice: auto / none / required / a specific tool
  5. Parallel tool calls -- run concurrently, return results together
  6. Tool DESIGN: why descriptions decide which tool gets picked (measured)
  7. Sizing tool results: the biggest silent context hog
  8. Safety: side effects, confirmation, idempotency, untrusted output
  9. Tools vs MCP vs agents -- where each word fits

Concepts:
  - Tool definition / schema: what the model reads to decide whether and how to call
  - Tool call: {id, name, arguments} written by the model
  - Tool result: your function's output, linked back by the call id
  - tool_choice: whether the model may / must / must not call tools
  - Parallel tool calls: several calls in ONE model turn

PREREQUISITES: Lesson 03. Pure Python, no packages, no credentials.

Run:  uv run python 07_tool_calling.py
"""

import asyncio
import inspect
import json
import math
import re
import time
from typing import Literal, get_args, get_origin, get_type_hints


def est_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


# ============================================================================
# The tools -- ordinary typed Python functions
# ============================================================================

ORDERS = [
    {"order_id": f"ORD-{1000 + i}", "customer_email": "sam@example.com" if i % 7 == 0 else f"user{i}@example.com",
     "status": ["open", "shipped", "cancelled"][i % 3], "total_eur": round(20 + i * 3.7, 2),
     "items": [f"item-{i}-{j}" for j in range(3)], "warehouse": "DUB-2", "internal_notes": "x" * 60}
    for i in range(200)
]


def get_weather(city: str, unit: Literal["c", "f"] = "c") -> dict:
    """Get the current weather for a city.

    Args:
        city: City name, e.g. "Rome".
        unit: Temperature unit, "c" for Celsius or "f" for Fahrenheit.
    """
    temp_c = {"rome": 24, "dublin": 14, "tokyo": 19}.get(city.lower(), 20)
    return {"city": city, "temp": temp_c if unit == "c" else round(temp_c * 9 / 5 + 32), "unit": unit}


def search_orders(customer_email: str,
                  status: Literal["open", "shipped", "cancelled", "any"] = "any",
                  limit: int = 5) -> dict:
    """Find a customer's orders, newest first. Use this before cancel_order to get the order id.

    Args:
        customer_email: The customer's email address.
        status: Only return orders with this status, or "any".
        limit: Maximum number of orders to return (1-20).
    """
    hits = [o for o in ORDERS if o["customer_email"] == customer_email
            and (status == "any" or o["status"] == status)]
    # Return only what the model needs -- see part 7.
    return {"count": len(hits), "orders": [
        {k: o[k] for k in ("order_id", "status", "total_eur")} for o in hits[:limit]]}


def cancel_order(order_id: str) -> dict:
    """Cancel an open order. This has a real side effect and cannot be undone.

    Args:
        order_id: The id from search_orders, e.g. "ORD-1007".
    """
    return {"order_id": order_id, "cancelled": True}


# ============================================================================
# PART 1: A tool definition -- generated from the function
# ============================================================================
# The model never sees your code. It sees ONLY: name, description, and a
# JSON Schema for the arguments. Writing schemas by hand drifts out of
# sync with the code, so frameworks generate them from type hints and
# docstrings (Pydantic, LangChain's @tool, FastMCP's @mcp.tool, the
# Anthropic SDK's @beta_tool). Here's the mechanism, in ~30 lines.

PY_TO_JSON = {str: "string", int: "integer", float: "number", bool: "boolean"}


def json_type(py_type) -> dict:
    if get_origin(py_type) is Literal:
        return {"type": "string", "enum": list(get_args(py_type))}
    if get_origin(py_type) is list:
        return {"type": "array", "items": json_type(get_args(py_type)[0])}
    return {"type": PY_TO_JSON[py_type]}


def function_to_tool(fn) -> dict:
    """Typed function + Google-style docstring -> a provider-neutral tool definition."""
    doc = inspect.getdoc(fn) or ""
    description = doc.split("\n\nArgs:")[0].strip()
    arg_docs = dict(re.findall(r"^\s{4}(\w+): (.+)$", doc, re.MULTILINE))
    hints = get_type_hints(fn)
    props, required = {}, []
    for name, param in inspect.signature(fn).parameters.items():
        prop = json_type(hints[name])
        if name in arg_docs:
            prop["description"] = arg_docs[name]
        if param.default is inspect.Parameter.empty:
            required.append(name)
        else:
            prop["default"] = param.default
        props[name] = prop
    return {"name": fn.__name__, "description": description,
            "parameters": {"type": "object", "properties": props,
                           "required": required, "additionalProperties": False}}


REGISTRY = {fn.__name__: fn for fn in (get_weather, search_orders, cancel_order)}
TOOL_DEFS = {name: function_to_tool(fn) for name, fn in REGISTRY.items()}


def to_openai(tool: dict) -> dict:
    return {"type": "function", "function": tool}


def to_anthropic(tool: dict) -> dict:
    return {"name": tool["name"], "description": tool["description"],
            "input_schema": tool["parameters"]}


def to_mcp(tool: dict) -> dict:
    return {"name": tool["name"], "description": tool["description"],
            "inputSchema": tool["parameters"]}


def part1_definitions():
    print("######## PART 1 -- What the model sees: the tool definition ########\n")
    print("  Python:\n")
    print("    def search_orders(customer_email: str,")
    print('                      status: Literal["open", "shipped", "cancelled", "any"] = "any",')
    print("                      limit: int = 5) -> dict:")
    print('        """Find a customer\'s orders, newest first. ..."""\n')
    print("  Generated definition (provider-neutral):\n")
    for line in json.dumps(TOOL_DEFS["search_orders"], indent=2).splitlines():
        print(f"    {line}")
    t = TOOL_DEFS["get_weather"]
    print("\n  Same tool, three wire formats -- only the wrapper differs:\n")
    print(f"    OpenAI    : {json.dumps(to_openai(t))[:88]}...")
    print(f"    Anthropic : {json.dumps(to_anthropic(t))[:88]}...")
    print(f"    MCP       : {json.dumps(to_mcp(t))[:88]}...")
    total = sum(est_tokens(json.dumps(d)) for d in TOOL_DEFS.values())
    print(f"\n  These 3 definitions cost ~{total} input tokens on EVERY call -- tools")
    print("  are context too (lesson 04). 50 tools can be thousands of tokens.\n")


# ============================================================================
# PART 1b: The COMPLETE tool definition -- all four parts
# ============================================================================
# The auto-generated schema above covers the minimum the API needs. A
# production tool definition documents four things:
#
#     1. Name and description     -- when to use it, what it does
#     2. Input / output schema    -- the arguments AND the shape of the result
#     3. Error handling           -- which errors it returns and how to recover
#     4. Usage examples           -- concrete calls, so the model copies the pattern
#
# Only the input schema is sent as structured JSON everywhere. The output
# schema is supported natively by MCP (outputSchema + structuredContent,
# see learn-mcp 04); errors and examples usually go into the description
# text, because that's what the model reads.

CANCEL_ORDER_SPEC = {
    "name": "cancel_order",
    "description": "Cancel an OPEN order by id. Irreversible. Call search_orders first to "
                   "find the id; only cancel orders the customer asked to cancel.",
    "input_schema": TOOL_DEFS["cancel_order"]["parameters"],
    "output_schema": {
        "type": "object",
        "properties": {"order_id": {"type": "string"}, "cancelled": {"type": "boolean"}},
        "required": ["order_id", "cancelled"],
    },
    "errors": {
        "ORDER_NOT_FOUND": "No order with that id -> call search_orders to get a valid id.",
        "NOT_CANCELLABLE": "Order is shipped/cancelled -> tell the user; offer refund_order instead.",
        "USER_DECLINED": "The user refused the confirmation -> do not retry; ask what they want.",
    },
    "examples": [
        {"user": "cancel my open order (I'm sam@example.com)",
         "calls": ['search_orders(customer_email="sam@example.com", status="open")',
                   'cancel_order(order_id="ORD-1000")']},
        {"user": "cancel ORD-1003 (already shipped)",
         "calls": ['cancel_order(order_id="ORD-1003") -> error NOT_CANCELLABLE -> explain, offer refund']},
    ],
}


def render_description(spec: dict) -> str:
    """Fold errors + examples into the description text the model reads."""
    lines = [spec["description"], "", "Errors:"]
    lines += [f"- {code}: {how}" for code, how in spec["errors"].items()]
    lines += ["", "Examples:"]
    for ex in spec["examples"]:
        lines.append(f"- User: {ex['user']!r} -> " + " then ".join(ex["calls"]))
    return "\n".join(lines)


def check_output(result: dict, schema: dict) -> list[str]:
    """Validate what YOUR tool returned -- catches tool bugs before the model sees them."""
    return [f"missing field '{f}'" for f in schema["required"] if f not in result]


def part1b_complete_definition():
    print("######## PART 1b -- The complete definition: 4 parts ########\n")
    spec = CANCEL_ORDER_SPEC
    print("  1. NAME + DESCRIPTION")
    print(f"     {spec['name']}: {spec['description']}\n")
    print("  2. INPUT SCHEMA (what the model must send)")
    print(f"     {json.dumps(spec['input_schema'])}")
    print("     OUTPUT SCHEMA (what your tool promises to return)")
    print(f"     {json.dumps(spec['output_schema'])}\n")
    print("  3. ERROR HANDLING (each error says how to RECOVER)")
    for code, how in spec["errors"].items():
        print(f"     {code:<16} {how}")
    print("\n  4. USAGE EXAMPLES")
    for ex in spec["examples"]:
        print(f"     user: {ex['user']!r}")
        for c in ex["calls"]:
            print(f"       -> {c}")
    print("\n  What the model actually receives as the description:\n")
    for line in render_description(spec).splitlines():
        print(f"     | {line}")
    good = cancel_order("ORD-1000")
    bad = {"order_id": "ORD-1000"}   # a buggy tool forgot a field
    print(f"\n  Output check on a good result : {check_output(good, spec['output_schema']) or 'OK'}")
    print(f"  Output check on a buggy result: {check_output(bad, spec['output_schema'])}\n")


# ============================================================================
# PART 2: Validation -- never trust the arguments
# ============================================================================
# The model generates arguments as TEXT. They can be missing, mistyped,
# out of the enum, or invented. Validate before running, and send
# problems back as a tool result -- the model reads it and retries.

def validate(args: dict, schema: dict) -> list[str]:
    errors = []
    props = schema["properties"]
    for req in schema["required"]:
        if req not in args:
            errors.append(f"missing required argument '{req}'")
    for name, value in args.items():
        if name not in props:
            errors.append(f"unknown argument '{name}' (allowed: {sorted(props)})")
            continue
        spec = props[name]
        expected = {"string": str, "integer": int, "number": (int, float), "boolean": bool}[spec["type"]]
        if not isinstance(value, expected) or (spec["type"] == "integer" and isinstance(value, bool)):
            errors.append(f"'{name}' must be {spec['type']}, got {type(value).__name__} {value!r}")
        elif "enum" in spec and value not in spec["enum"]:
            errors.append(f"'{name}' must be one of {spec['enum']}, got {value!r}")
    return errors


# ============================================================================
# PART 3: The round trip -- exact messages
# ============================================================================

class ScriptedModel:
    """Stand-in model: replays what a real model typically does in this
    conversation -- including a realistic mistake on the first call."""

    def __init__(self):
        self.turn = 0

    def reply(self, messages: list[dict]) -> dict:
        self.turn += 1
        if self.turn == 1:    # wrong argument name + wrong type
            return {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_1", "name": "search_orders",
                 "arguments": {"email": "sam@example.com", "status": "open", "limit": "five"}}]}
        if self.turn == 2:    # read the error, fixed the call
            return {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_2", "name": "search_orders",
                 "arguments": {"customer_email": "sam@example.com", "status": "open", "limit": 5}}]}
        if self.turn == 3:    # picks the id FROM the tool result
            result = json.loads(messages[-1]["content"])
            oid = result["orders"][0]["order_id"]
            return {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_3", "name": "cancel_order", "arguments": {"order_id": oid}}]}
        last = json.loads(messages[-1]["content"])
        return {"role": "assistant", "content": f"Done -- order {last['order_id']} is cancelled.",
                "tool_calls": None}


SIDE_EFFECT_TOOLS = {"cancel_order"}


def approve(name: str, args: dict) -> bool:
    """The permission gate. A real app asks the user; the demo auto-approves."""
    print(f"      [gate] '{name}' has side effects -> asking user to confirm {args} ... approved")
    return True


def execute(call: dict) -> tuple[str, bool]:
    """Returns (content, is_error). Errors are RESULTS, not exceptions."""
    fn = REGISTRY.get(call["name"])
    if fn is None:
        return json.dumps({"error": f"unknown tool {call['name']!r}"}), True
    errors = validate(call["arguments"], TOOL_DEFS[call["name"]]["parameters"])
    if errors:
        return json.dumps({"error": "invalid arguments", "details": errors}), True
    if call["name"] in SIDE_EFFECT_TOOLS and not approve(call["name"], call["arguments"]):
        return json.dumps({"error": "user declined this action"}), True
    try:
        return json.dumps(fn(**call["arguments"])), False
    except Exception as e:                       # a crash becomes information for the model
        return json.dumps({"error": f"{type(e).__name__}: {e}"}), True


def part3_round_trip():
    print("######## PART 2+3 -- The round trip, with validation ########\n")
    model = ScriptedModel()
    messages = [
        {"role": "system", "content": "You are a support agent. Use tools to act."},
        {"role": "user", "content": "Cancel my open order please. I'm sam@example.com"},
    ]
    for step in range(1, 6):
        reply = model.reply(messages)
        messages.append(reply)
        if not reply["tool_calls"]:
            print(f"  model #{step} -> TEXT: {reply['content']!r}   (stop_reason: end_turn)\n")
            break
        for call in reply["tool_calls"]:
            print(f"  model #{step} -> TOOL CALL {call['name']}({call['arguments']})")
            content, is_error = execute(call)
            print(f"      result{' (is_error)' if is_error else ''}: {content}")
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": content})
        print()

    print("  The model got it wrong once, READ the error, and fixed it. Returning")
    print("  errors as results (not raising) is what makes agents robust.\n")
    print("  The same conversation on the wire:\n")
    print("  OpenAI Chat Completions:")
    print('    assistant: {"role": "assistant", "tool_calls": [{"id": "call_2", "type": "function",')
    print('                "function": {"name": "search_orders", "arguments": "{\\"customer_email\\": ..."}}]}')
    print('                                          ^ arguments is a JSON STRING -- json.loads() it')
    print('    you      : {"role": "tool", "tool_call_id": "call_2", "content": "{\\"count\\": 10, ...}"}')
    print("\n  Anthropic Messages:")
    print('    assistant: {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_02",')
    print('                "name": "search_orders", "input": {"customer_email": ...}}]}')
    print('                                          ^ input is already an object')
    print('    you      : {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_02",')
    print('                "content": "...", "is_error": false}]}')
    print("                                          ^ results go in a USER message\n")


# ============================================================================
# PART 4: tool_choice
# ============================================================================

def part4_tool_choice():
    print("######## PART 4 -- tool_choice ########\n")
    rows = [
        ("auto (default)", '"auto" / {"type": "auto"}', "Model decides: answer directly or call tools",
         "Almost always"),
        ("none", '"none" / {"type": "none"}', "Tools listed but calling is off",
         "A final summarize-only turn"),
        ("required / any", '"required" / {"type": "any"}', "Must call SOME tool",
         "Pipelines that always need a lookup"),
        ("a specific tool", '{"type": "function", "function": {"name": X}} /\n'
         f"{'':<22}{'':<3}" + '{"type": "tool", "name": X}', "Must call exactly X",
         "Old trick for JSON extraction"),
    ]
    for name, syntax, effect, when in rows:
        print(f"  {name:<20} {effect}")
        print(f"  {'':<20} syntax (OpenAI / Anthropic): {syntax}")
        print(f"  {'':<20} use for: {when}\n")
    print("  Notes:")
    print("   - Forcing a tool just to get JSON is outdated -- use structured outputs.")
    print("   - Some of the newest reasoning models REJECT forced tool choice")
    print("     ('required'/'any'/specific). Use auto + a clear instruction instead.")
    print("   - parallel_tool_calls=False (OpenAI) / disable_parallel_tool_use")
    print("     (Anthropic) limits the model to one call per turn.\n")


# ============================================================================
# PART 5: Parallel tool calls
# ============================================================================

async def slow_weather(city: str) -> dict:
    await asyncio.sleep(0.3)            # simulated network latency
    return get_weather(city)


async def part5_parallel():
    print("######## PART 5 -- Parallel tool calls ########\n")
    calls = [{"id": f"call_{c}", "name": "get_weather", "arguments": {"city": c}}
             for c in ("Rome", "Dublin", "Tokyo")]
    print("  User: 'Compare the weather in Rome, Dublin and Tokyo.'")
    print(f"  ONE model turn contains {len(calls)} tool calls:")
    for c in calls:
        print(f"    {c['name']}({c['arguments']})")

    t = time.perf_counter()
    for c in calls:
        await slow_weather(**c["arguments"])
    seq = time.perf_counter() - t
    t = time.perf_counter()
    results = await asyncio.gather(*(slow_weather(**c["arguments"]) for c in calls))
    par = time.perf_counter() - t
    print(f"\n  run one by one : {seq:.1f}s")
    print(f"  run concurrently: {par:.1f}s  (asyncio.gather)\n")
    print("  Send ALL results back together, each linked to its call id:")
    for c, r in zip(calls, results):
        print(f"    tool_result {c['id']:<12} -> {r}")
    print("\n  (On Anthropic: every tool_result in ONE user message. Splitting them")
    print("   across messages teaches the model to stop making parallel calls.)\n")


# ============================================================================
# PART 6: Tool design -- descriptions decide what gets called
# ============================================================================
# The ONLY thing the model knows about a tool is its name, description
# and schema. The stand-in "model" below picks the tool whose name +
# description best overlaps the request. Real models are far smarter,
# but they have the same information bottleneck -- measured effect,
# same direction.

VAGUE_TOOLS = {
    "tool_a": "Handles orders.",
    "tool_b": "Order operations.",
    "tool_c": "Gets info.",
    "tool_d": "Utility function.",
}
CLEAR_TOOLS = {
    "search_orders": "Find or look up a customer's orders by email. Returns order ids, status, totals.",
    "cancel_order": "Cancel an open order by order id. Cannot be undone.",
    "get_weather": "Current weather and temperature for a city.",
    "refund_order": "Refund a shipped or delivered order's payment back to the customer.",
}
VAGUE_TRUTH = {"search_orders": "tool_a", "cancel_order": "tool_b",
               "get_weather": "tool_c", "refund_order": "tool_d"}

REQUESTS = [
    ("find the orders for sam@example.com", "search_orders"),
    ("look up my orders", "search_orders"),
    ("cancel order ORD-1007", "cancel_order"),
    ("please cancel my open order", "cancel_order"),
    ("what's the temperature in Rome", "get_weather"),
    ("is it raining in Dublin, what's the weather", "get_weather"),
    ("refund my payment for the shipped order", "refund_order"),
    ("I want my money back for a delivered order", "refund_order"),
]


def pick_tool(request: str, tools: dict[str, str]) -> str:
    words = lambda s: set(re.findall(r"[a-z]{2,}", s.lower())) - {"the", "my", "for", "an", "or", "by", "is", "in"}
    return max(tools, key=lambda n: len(words(request) & words(n.replace("_", " ") + " " + tools[n])))


def part6_design():
    print("######## PART 6 -- Tool design ########\n")
    vague = sum(pick_tool(r, VAGUE_TOOLS) == VAGUE_TRUTH[t] for r, t in REQUESTS)
    clear = sum(pick_tool(r, CLEAR_TOOLS) == t for r, t in REQUESTS)
    print(f"  vague names + descriptions ('tool_a: Handles orders.')  -> {vague}/{len(REQUESTS)} right tool")
    print(f"  clear names + descriptions                             -> {clear}/{len(REQUESTS)} right tool\n")
    print("""  Design rules:
   - Name = verb_noun, unambiguous: search_orders, not orders / tool_a.
   - Description = when to use it, what it returns, what NOT to use it for,
     and how it relates to other tools ("use search_orders first").
   - Describe every parameter, with an example ("e.g. ORD-1007") and units.
   - Enums over free text wherever the set of values is known.
   - Fewer, distinct tools beat many overlapping ones (context 'confusion').
   - Return errors that say how to FIX the call, not just that it failed.
   - Tool descriptions are prompts: version them and eval them.
""")


# ============================================================================
# PART 7: Tool results are context -- size them
# ============================================================================

def part7_result_size():
    print("######## PART 7 -- Sizing tool results ########\n")
    email = "sam@example.com"
    raw = json.dumps([o for o in ORDERS if o["customer_email"] == email] and ORDERS)   # a lazy "return everything"
    shaped = json.dumps(search_orders(email, "any", 5))
    print(f"  return every order, every field : {est_tokens(raw):>6} tokens")
    print(f"  filtered, 3 fields, limit 5     : {est_tokens(shaped):>6} tokens\n")
    print("""  A tool result stays in the context for the REST of the conversation and
  is resent on every later call (lesson 03). Shape results for the model:
   - filter server-side; paginate (limit + "count" so the model knows there's more)
   - return only the fields the model needs; drop internal notes and blobs
   - return ids the next tool takes, so the model can chain calls
   - summarise huge outputs (logs, pages) -- or hand them to a subagent
""")


# ============================================================================
# PART 8: Safety
# ============================================================================

def part8_safety():
    print("######## PART 8 -- Safety ########\n")
    print("""  [ ] Validate every argument against the schema (part 2) -- never eval() or
      pass model text straight into SQL / shell / file paths
  [ ] Classify tools: read-only (auto-run) vs side effects (confirm first)
  [ ] Least privilege: the tool's credentials can only do what the tool says
  [ ] Idempotency: a retried create_ticket / send_email must not duplicate
  [ ] Scope to the user: search_orders must only see the CALLER's orders --
      enforce in code, not by trusting the model to pass the right email
  [ ] Tool OUTPUT is untrusted: a web page or email saying "ignore your rules"
      is prompt injection (learn-ai-advanced 04)
  [ ] Cap tool calls per request (an agent loop can call tools forever)
  [ ] Log every call: name, args, result size, latency, approved-by
""")


# ============================================================================
# PART 9: Tools vs MCP vs agents
# ============================================================================

def part9_vocabulary():
    print("######## PART 9 -- Tools vs MCP vs agents ########\n")
    print("""  | Term           | What it is                                           | Where in this repo        |
  |----------------|------------------------------------------------------|---------------------------|
  | Tool call      | ONE request/result round trip (this lesson)          | 03, 07                    |
  | Agent          | A LOOP of tool calls until the model stops asking    | learn-mini-claude 01-05   |
  | MCP            | A PROTOCOL for serving tool definitions + running    | learn-mcp 01-16,          |
  |                | tools in a separate process, reusable by any client  | learn-mini-claude 03      |
  | Server tools   | Tools the PROVIDER runs for you (web search, code    | provider docs             |
  |                | execution) -- no round trip through your code        |                           |
  | Subagent       | An agent exposed as a tool to another agent          | learn-mini-claude 06      |

  MCP doesn't change the model's side at all: the client fetches tool
  definitions from an MCP server, sends them to the model exactly as in
  part 1, and forwards the model's calls to the server.
""")


def main():
    part1_definitions()
    part1b_complete_definition()
    part3_round_trip()
    part4_tool_choice()
    asyncio.run(part5_parallel())
    part6_design()
    part7_result_size()
    part8_safety()
    part9_vocabulary()


if __name__ == "__main__":
    main()

    # -- Key takeaway --------------------------------------------------------
    # Tool calling = the model WRITES a structured request; your code
    # validates, gates, runs, and returns the result as more context.
    #   - The definition (name, description, schema) is the model's only
    #     documentation -- design it like an API for a new colleague.
    #   - Validate args, return errors as results, confirm side effects.
    #   - Run parallel calls concurrently; return results together.
    #   - Keep results small -- they stay in the context forever.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add `def convert_currency(amount: float, to: Literal["EUR","USD","GBP"])`
    #    to REGISTRY and print its generated definition.
    # 2. Make ScriptedModel call "cancel_ordr" (typo). What does execute()
    #    return? How would the model recover?
    # 3. Change approve() to return False. What does the model receive,
    #    and what should its next message say?
    # 4. Make search_orders enforce the caller: take `caller_email` from the
    #    session, NOT from the model's arguments (part 8).
