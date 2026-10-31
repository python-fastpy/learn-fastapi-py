"""09 -- Agent: tool calling in a loop until the GOAL is done
============================================================

CONCEPT IN ONE LINE:
  An agent = LLM + tools + a loop. The model decides the next step each time,
  using the results of the previous steps.                     (details: simple/09)

   goal: "Refund the last order of customer ana@example.com"
     │
     ▼
   ┌─▶ model decides next step ──▶ find_customer("ana@example.com") ──▶ {"id": "C7"}
   │                         ──▶ get_orders("C7")                 ──▶ [O-55, O-31]
   │                         ──▶ refund("O-55")                   ──▶ {"ok": true}
   │       │
   │   no more tools needed? ── yes ──▶ final answer
   │       │ no
   │   step limit reached? ──── yes ──▶ STOP (protects you from endless loops / cost)
   └───────┘

  Difference from lesson 08: here the model chains SEVERAL steps, and each step
  depends on the result of the step before.
"""

import json

from ollama_client import chat

CUSTOMERS = {"ana@example.com": "C7"}
ORDERS = {"C7": [{"id": "O-55", "date": "2026-10-20", "total": 40},
                 {"id": "O-31", "date": "2026-09-02", "total": 15}]}


def find_customer(email):
    return {"customer_id": CUSTOMERS.get(email, "not found")}


def get_orders(customer_id):
    return {"orders": ORDERS.get(customer_id, [])}


def refund(order_id):
    return {"order_id": order_id, "refunded": True}       # real app: ask a human first!


FUNCTIONS = {"find_customer": find_customer, "get_orders": get_orders, "refund": refund}


def tool(name, description, param):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "required": [param],
                       "properties": {param: {"type": "string"}}}}}


TOOLS = [tool("find_customer", "Find a customer id by email", "email"),
         tool("get_orders", "List a customer's orders, newest first", "customer_id"),
         tool("refund", "Refund one order by id", "order_id")]


def run_agent(goal, max_steps=6):
    messages = [{"role": "system", "content": "You are a support agent. Use the tools step by step. "
                                              "Call one tool at a time."},
                {"role": "user", "content": goal}]
    for step in range(1, max_steps + 1):
        msg = chat(messages, tools=TOOLS, options={"temperature": 0})["message"]
        messages.append(msg)
        if not msg.get("tool_calls"):
            print(f"  step {step}: DONE -> {msg['content']}")
            return
        for call in msg["tool_calls"]:
            name, args = call["function"]["name"], call["function"]["arguments"]
            try:                                              # the model can send wrong args
                result = FUNCTIONS[name](**args) if name in FUNCTIONS else {"error": "unknown tool"}
            except TypeError as e:
                result = {"error": f"bad arguments: {e}"}
            print(f"  step {step}: {name}({args}) -> {result}")
            messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result)})
    print(f"  STOPPED: reached max_steps={max_steps}")


def main():
    print("GOAL: Refund the most recent order of customer ana@example.com\n")
    run_agent("Refund the most recent order of customer ana@example.com.")
    print("\nREMEMBER:")
    print("  - Always set max_steps (cost + safety).")
    print("  - Small models (3B) sometimes skip a step or pick a wrong order.")
    print("    Bigger models do better -- and risky tools need human approval.")


if __name__ == "__main__":
    main()
