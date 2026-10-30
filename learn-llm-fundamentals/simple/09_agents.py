"""09 -- AI agents  (simple version)
==================================

IN ONE LINE:
  An agent is an LLM in a loop. Each turn the MODEL picks the next step:
  call a tool, or give the final answer. YOUR code runs the loop.

REAL USE CASE:
  A user tells your FastAPI support bot "Refund Sam Lee's last order".
  One model call is not enough. The agent needs several tools in a row:

       task
         │
         ▼
     ┌─────────┐  final answer   ┌──────┐
  ┌─▶│  MODEL  │ ──────────────▶ │ done │
  │  └─────────┘                 └──────┘
  │       │ tool call
  │       ▼
  │  ┌──────────────────────────────┐
  │  │ YOUR CODE: step limit check  │
  │  │ -> run tool -> add result    │
  │  └──────────────────────────────┘
  └───────┘  (loop again)

WHERE THE AGENT SITS IN A REAL APP:

  ┌──────────────┐  POST /chat   ┌─────────────────────────────┐  HTTPS   ┌──────────────────┐
  │   Browser    │ ────────────▶ │  YOUR FASTAPI               │ ───────▶ │   LLM PROVIDER   │
  │ "Refund Sam  │               │  run_agent() loop:          │ messages │  decides ONE     │
  │  Lee's last  │               │   - sends messages          │ ◀─────── │  next step:      │
  │  order"      │               │   - runs the tool it picked │ decision │  tool or answer  │
  │              │ ◀──────────── │   - counts steps            │          └──────────────────┘
  └──────────────┘  final answer └─────────────────────────────┘
                                        │ ▲
                              tool call │ │ result
                                        ▼ │
                                 ┌──────────────────────────────────┐
                                 │ YOUR TOOLS (DB, payments API...) │
                                 │ find_customer, get_orders,       │
                                 │ refund_order                     │
                                 └──────────────────────────────────┘
  The model NEVER runs a tool itself. It only ASKS. Your code runs it.

THE MESSAGES LIST GROWS EACH STEP (this is the agent's "memory"):

  start:        [user: task]
  after step 1: [user: task, assistant: find_customer, tool: {customer_id}]
  after step 2: [ ... , assistant: get_orders,   tool: {orders}]
  after step 3: [ ... , assistant: refund_order, tool: {refunded}]
  step 4:       model reads ALL of it and gives the final answer
  Each step = one more model call, and the model sees a longer list each time.

GOOD RUN, step by step (the real run printed by STEP 2 + 3, max_steps = 5):

   step   model decides (thought)        tool + args                    result
   ────   ───────────────────────────    ───────────────────────────    ──────────────────────────────
   1      "who is Sam Lee?"              find_customer                  {'customer_id': 'C-101'}
                                         {'name': 'Sam Lee'}
   2      "what did C-101 buy?"          get_orders                     {'orders': [ORD-3 80.0,
                                         {'customer_id': 'C-101'}                   ORD-7 34.5]}
   3      "last order = ORD-7"           refund_order                   {'refunded': True,
                                         {'order_id': 'ORD-7'}           'order_id': 'ORD-7'}
   4      "I have everything"            (no tool)                      final answer: "Done. I refunded
                                                                        order ORD-7 for Sam Lee."
   stop reason: final_answer   (4 of 5 allowed steps used)

STUCK RUN (the real run printed by STEP 4, max_steps = 3):

   step   tool + args                       result
   ────   ───────────────────────────────   ────────────────────────
   1      find_customer {'name': 'Sam Lee'} {'customer_id': 'C-101'}
   2      find_customer {'name': 'Sam Lee'} {'customer_id': 'C-101'}   ◀── same again
   3      find_customer {'name': 'Sam Lee'} {'customer_id': 'C-101'}   ◀── and again
   ──▶    step 3 == max_steps  ──▶  "stopped: hit max_steps = 3"
   stop reason: max_steps   (without the limit, this loops and costs money forever)

WHAT AN ENGINEER MUST KNOW:
  1. Agent = model + tools + loop. The model decides the steps.
  2. ALWAYS have a step limit. Without it, a confused model loops forever
     (and costs money on every call).
  3. Tool errors go BACK to the model as results, so it can fix itself.
  4. Risky tools (refunds, deletes) should need a human approval.
  5. If a fixed list of steps works, use normal code (a "workflow").
     Use an agent only when the steps are not known in advance.

Run:  uv run python simple/09_agents.py
"""

# ----------------------------------------------------------------------------
# STEP 1: TOOLS = normal Python functions the model is allowed to call
# ----------------------------------------------------------------------------
#   tool name         input (args)                 output (result)
#   ───────────────   ──────────────────────────   ────────────────────────────────────────
#   find_customer ──▶ {"name": "Sam Lee"}      ──▶ {"customer_id": "C-101"}
#                     (name not in CUSTOMERS)  ──▶ {"error": "NOT_FOUND: no customer named ..."}
#   get_orders    ──▶ {"customer_id": "C-101"} ──▶ {"orders": [ORD-3 80.0, ORD-7 34.5]}
#   refund_order  ──▶ {"order_id": "ORD-7"}    ──▶ {"refunded": True, "order_id": "ORD-7"}
#
#   TOOLS dict = name ──▶ function. The model sends a NAME, your code looks it up.
#   An error is a normal result (a dict), NOT a crash. The model reads it and can retry.
CUSTOMERS = {"Sam Lee": "C-101"}
ORDERS = {"C-101": [{"order_id": "ORD-3", "total": 80.0}, {"order_id": "ORD-7", "total": 34.5}]}


def find_customer(name):
    if name not in CUSTOMERS:
        return {"error": "NOT_FOUND: no customer named " + name}
    return {"customer_id": CUSTOMERS[name]}


def get_orders(customer_id):
    return {"orders": ORDERS.get(customer_id, [])}


def refund_order(order_id):
    return {"refunded": True, "order_id": order_id}


TOOLS = {"find_customer": find_customer, "get_orders": get_orders, "refund_order": refund_order}


# ----------------------------------------------------------------------------
# STEP 2: FAKE MODEL = looks at the messages so far and picks the next step
# ----------------------------------------------------------------------------
#   messages ──▶ count the "tool" results so far ──▶ step
#                                                     │
#      step 0? ── yes ──▶ {"tool": "find_customer", "args": {"name": "Sam Lee"}}
#        │ no
#        ▼
#      step 1? ── yes ──▶ read customer_id "C-101" from result 1
#        │ no             ──▶ {"tool": "get_orders", "args": {"customer_id": "C-101"}}
#        ▼
#      step 2? ── yes ──▶ read orders from result 2, take the LAST one ("ORD-7")
#        │ no             ──▶ {"tool": "refund_order", "args": {"order_id": "ORD-7"}}
#        ▼
#      {"answer": "Done. I refunded order ORD-7 for Sam Lee."}
#
#   A real model does the same job: it reads the whole list and picks the next step.
#   stuck_llm ignores the list and ALWAYS returns find_customer -> it never finishes.
# A real call looks like this (Anthropic SDK):
#   response = client.messages.create(model="...", max_tokens=1024,
#                                     tools=TOOL_SCHEMAS, messages=messages)
#   if response.stop_reason == "tool_use": ...run the tool...
def fake_llm(messages):
    """Count tool results so far, and return the next scripted step."""
    tool_results = [m for m in messages if m["role"] == "tool"]
    step = len(tool_results)
    if step == 0:
        return {"tool": "find_customer", "args": {"name": "Sam Lee"}}
    if step == 1:
        customer_id = tool_results[0]["content"]["customer_id"]
        return {"tool": "get_orders", "args": {"customer_id": customer_id}}
    if step == 2:
        last_order = tool_results[1]["content"]["orders"][-1]    # most recent order
        return {"tool": "refund_order", "args": {"order_id": last_order["order_id"]}}
    return {"answer": "Done. I refunded order ORD-7 for Sam Lee."}


def stuck_llm(messages):
    """A broken model that never stops. Shows why the step limit matters."""
    return {"tool": "find_customer", "args": {"name": "Sam Lee"}}


# ----------------------------------------------------------------------------
# STEP 3: THE AGENT LOOP = ask model -> run tool -> add result -> repeat
# ----------------------------------------------------------------------------
#   messages = [{"role": "user", "content": "Refund Sam Lee's last order"}]
#      │
#      ▼
#   ┌─▶ step > max_steps? ── yes ──▶ END: print "stopped: hit max_steps", return "max_steps"
#   │      │ no
#   │      ▼
#   │   decision = llm(messages)  ──▶ e.g. {"tool": "get_orders", "args": {"customer_id": "C-101"}}
#   │      │
#   │      ▼
#   │   "answer" in decision? ── yes ──▶ END: print final answer, return "final_answer"
#   │      │ no
#   │      ▼
#   │   tool name in TOOLS? ── no ──▶ result = {"error": "UNKNOWN_TOOL ..."} no crash ─┐
#   │      │ yes                                                                       │
#   │      ▼                                                                           │
#   │   result = TOOLS[name](**args) ──▶ {"orders": [ORD-3 80.0, ORD-7 34.5]}          │
#   │      │ ◀─────────────────────────────────────────────────────────────────────────┘
#   │      ▼
#   │   messages.append(assistant: decision)
#   │   messages.append(tool: result)       ◀── the model will see this next turn
#   │      │
#   └──────┘  step = step + 1
def run_agent(task, llm, max_steps=5):
    messages = [{"role": "user", "content": task}]
    for step in range(1, max_steps + 1):          # the step limit: NEVER loop forever
        decision = llm(messages)
        if "answer" in decision:                  # the model says it is done
            print("  step", step, ": final answer ->", decision["answer"])
            return "final_answer"
        name = decision["tool"]
        if name in TOOLS:
            result = TOOLS[name](**decision["args"])
        else:
            result = {"error": "UNKNOWN_TOOL " + name}   # error goes back, no crash
        print("  step", step, ":", name, decision["args"], "->", result)
        messages.append({"role": "assistant", "content": decision})
        messages.append({"role": "tool", "content": result})
    print("  stopped: hit max_steps =", max_steps)
    return "max_steps"


def main():
    print("STEP 1: tools the agent can use")
    print("  ", list(TOOLS))

    print("\nSTEP 2 + 3: a good run (the model picks each step)")
    reason = run_agent("Refund Sam Lee's last order", fake_llm)
    print("  stop reason:", reason)

    print("\nSTEP 4: a stuck model (the step limit saves you)")
    reason = run_agent("Refund Sam Lee's last order", stuck_llm, max_steps=3)
    print("  stop reason:", reason)


if __name__ == "__main__":
    main()

# Remember:
#   - Agent = LLM + tools + a loop where the model picks the next step.
#   - Always set max_steps (and log WHY the loop stopped).
#   - Return tool errors to the model; ask a human before risky actions.
# Try: in run_agent, when name is "refund_order", do not run it. Use
#      result = {"error": "NEEDS_HUMAN_APPROVAL"} instead, and run again.
