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
