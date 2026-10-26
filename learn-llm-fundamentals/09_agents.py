"""Lesson 09 -- AI agents: an LLM in a loop, choosing its own next step
======================================================================

WHY THIS MATTERS:
  Lesson 07 was ONE tool round trip. Put that round trip in a LOOP, let
  the model decide each turn whether to call another tool or stop, and
  you have an AGENT. Coding assistants, support bots that "do things",
  research assistants -- all of them are this loop plus guard rails.
  Almost every agent bug (runaway costs, infinite loops, wrong refunds)
  lives in the loop code YOU write, not in the model.

Flow:
      task
        |
        v
   +-> MODEL: "what next?" (think) --- final answer? ---> done
   |     | tool call (act)
   |     v
   |   YOUR CODE: stop checks -> approval gate -> run tool
   |     | tool result (observe)
   +-----+

WHAT YOU'LL LEARN:
  1. What an agent is: LLM + tools + a loop where the MODEL picks the step
  2. Stopping conditions: answer, max_steps, budget, repeats, escalation
  3. ReAct (think/act/observe each step) vs plan-then-execute
  4. Workflows vs agents: chaining, routing, parallelization,
     orchestrator-workers, evaluator-optimizer -- and when to use which
  5. Memory: short-term (messages), scratchpad, long-term (store + retrieve)
  6. Subagents: isolated contexts that return only a summary (measured)
  7. Errors and recovery: self-correction, retries, human approval
  8. Evaluating agents: success rate, steps and cost per task
  9. Where frameworks and MCP fit in the stack

Concepts:
  - Agent loop: call model -> run requested tool -> append result -> repeat
  - Stop reason: WHY the loop ended (final_answer, max_steps, budget, ...)
  - Workflow: YOUR code fixes the steps; agent: the MODEL chooses them
  - Subagent: an agent run with a fresh context, called like a tool
  - Human-in-the-loop (HITL): a person approves risky actions

PREREQUISITES: Lessons 01-03 and 07. Pure Python, no packages, no credentials.

Run:  uv run python 09_agents.py
"""

import copy
import json
import math
import random
import re
from collections import Counter


def est_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def short(text: str, n: int = 66) -> str:
    return text if len(text) <= n else text[: n - 3] + "..."


# ============================================================================
# The world: a tiny shop, its tools, and a scripted stand-in model
# ============================================================================

SYSTEM = ("You are a support agent. Policy: refund the customer's MOST RECENT order "
          "only if it is under $50; otherwise escalate to a human.")
TOOL_SPECS = {
    "find_customer": "Look up a customer id by full name.",
    "get_orders": "List a customer's orders. Needs customer_id like 'C-101'.",
    "refund_order": "Refund an order. SIDE EFFECT: moves money.",
    "escalate_to_human": "Hand the case to a human. Ends the run.",
    "search_kb": "Search the help-centre knowledge base.",
}
TOOLS_TOKENS = est_tokens(json.dumps(TOOL_SPECS))   # sent on EVERY call (lesson 07)
PRICE_IN, PRICE_OUT = 3 / 1e6, 15 / 1e6              # illustrative $ per token

BASE_DB = {
    "customers": {"Sam Lee": "C-101", "Ana Ruiz": "C-102", "Bo Chen": "C-103"},
    "orders": {
        "C-101": [{"order_id": "ORD-3", "total": 80.0, "date": "2026-09-01"},
                  {"order_id": "ORD-7", "total": 34.5, "date": "2026-10-20"}],
        "C-102": [{"order_id": "ORD-9", "total": 120.0, "date": "2026-10-11"}],
        "C-103": [],
    },
}
DB: dict = {}
LEDGER: list = []          # every refund that really happened


def reset(db=None):
    DB.clear()
    DB.update(copy.deepcopy(db or BASE_DB))
    LEDGER.clear()


def find_customer(name: str) -> dict:
    cid = DB["customers"].get(name)
    return {"customer_id": cid} if cid else {"error": f"NOT_FOUND: no customer named {name!r}."}


def get_orders(customer_id: str) -> dict:
    if not re.fullmatch(r"C-\d+", customer_id):
        return {"error": f"INVALID_ID: customer_id must look like 'C-101', got {customer_id!r}. "
                         "Call find_customer first."}
    return {"orders": DB["orders"].get(customer_id, [])}


def refund_order(order_id: str, amount: float) -> dict:
    LEDGER.append((order_id, amount))
    return {"refunded": True, "order_id": order_id, "amount": amount}


def search_kb(query: str) -> dict:
    return {"hits": []}


TOOLS = {f.__name__: f for f in (find_customer, get_orders, refund_order, search_kb)}
RISKY = {"refund_order"}


def execute(name: str, args: dict, approve=None) -> dict:
    """Run a tool. Errors come back as RESULTS so the model can react (lesson 07)."""
    if name not in TOOLS:
        return {"error": f"UNKNOWN_TOOL {name!r}"}
    if name in RISKY and approve is not None and not approve(name, args):
        return {"error": "USER_DECLINED: a human rejected this action. Do not retry."}
    try:
        return TOOLS[name](**args)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def act(thought, tool, args):
    return {"role": "assistant", "thought": thought, "tool_call": {"name": tool, "args": args}}


def final(thought, answer):
    return {"role": "assistant", "thought": thought, "content": answer}


def last_result(messages, tool):
    for m in reversed(messages):
        if m["role"] == "tool" and m["name"] == tool:
            return json.loads(m["content"])
    return None


def task_for(name):
    return f"Find the last order for customer '{name}' and refund it if it is under $50."


class RefundModel:
    """Stand-in LLM. Like a real one, it decides the next step by READING the
    conversation so far -- not from a fixed script of turns."""

    def __init__(self, error_rate=0.0, seed=0, sloppy=False):
        self.rng, self.error_rate, self.sloppy = random.Random(seed), error_rate, sloppy

    def reply(self, messages):
        name = re.search(r"'([^']+)'", messages[1]["content"]).group(1)
        cust = last_result(messages, "find_customer")
        if cust is None:
            return act("I need the customer's id before I can see orders.", "find_customer", {"name": name})
        if "error" in cust:
            return final("Lookup failed; I must not guess an id.", f"I couldn't find a customer named {name!r}.")
        orders = last_result(messages, "get_orders")
        if orders is None:
            cid = name if self.sloppy else cust["customer_id"]      # sloppy = a realistic slip
            return act("Got the id. Now list their orders.", "get_orders", {"customer_id": cid})
        if "error" in orders:
            return act("The error says: use the id from find_customer. Retrying.",
                       "get_orders", {"customer_id": cust["customer_id"]})
        if not orders["orders"]:
            return final("Nothing to refund.", f"{name} has no orders.")
        refund = last_result(messages, "refund_order")
        if refund is not None:
            if "error" in refund:
                return final("The refund was blocked.", f"No refund made ({refund['error'].split(':')[0]}).")
            return final("The tool confirmed it.", f"Refunded {refund['order_id']} (${refund['amount']:.2f}).")
        newest = max(orders["orders"], key=lambda o: o["date"])
        if self.rng.random() < self.error_rate:
            newest = orders["orders"][0]                            # misreads "last" as first
        oid, total = newest["order_id"], newest["total"]
        if total < 50:
            return act(f"Newest is {oid} at ${total:.2f} < $50 -> refund allowed.",
                       "refund_order", {"order_id": oid, "amount": total})
        return act(f"Newest is {oid} at ${total:.2f} >= $50 -> a human must decide.",
                   "escalate_to_human", {"order_id": oid, "reason": "over $50 limit"})


# ============================================================================
# PART 1: What an agent is -- the loop
# ============================================================================
#   single call          fixed workflow              agent
#   ┌─────┐              ┌───┐  ┌───┐  ┌───┐         ┌───────┐ tool ┌──────┐
#   │ LLM │─▶ text       │ A │─▶│ B │─▶│ C │         │  LLM  │─────▶│ tool │
#   └─────┘              └───┘  └───┘  └───┘         └───────┘◀─────└──────┘
#   can't act            CODE picks the steps        MODEL picks the next step,
#                                                    until it answers ✓

def run_agent(model, task, max_steps=8, max_tokens=None, max_repeats=2, approve=None, verbose=False):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
    seen, usage = Counter(), {"calls": 0, "tok_in": 0, "tok_out": 0, "context": []}

    def finish(stop, answer=None):
        if verbose:
            print(f"  STOP -> {stop}\n")
        cost = usage["tok_in"] * PRICE_IN + usage["tok_out"] * PRICE_OUT
        return {"stop": stop, "answer": answer, "messages": messages, "cost": cost, **usage}

    for step in range(1, max_steps + 1):
        if max_tokens and usage["tok_in"] + usage["tok_out"] >= max_tokens:
            return finish("budget")
        ctx = est_tokens(json.dumps(messages)) + TOOLS_TOKENS
        reply = model.reply(messages)                       # THINK
        usage["calls"] += 1
        usage["tok_in"] += ctx
        usage["tok_out"] += est_tokens(json.dumps(reply))
        usage["context"].append(ctx)
        messages.append(reply)
        if verbose:
            print(f"  step {step} (context {ctx} tok)\n    thought: {reply['thought']}")
        if "content" in reply:
            if verbose:
                print(f"    ANSWER : {reply['content']}")
            return finish("final_answer", reply["content"])
        call = reply["tool_call"]                           # ACT
        if verbose:
            print(f"    action : {call['name']}({json.dumps(call['args'])})")
        key = (call["name"], json.dumps(call["args"], sort_keys=True))
        seen[key] += 1
        if seen[key] > max_repeats:
            return finish("repeated_action")
        if call["name"] == "escalate_to_human":
            return finish("escalated", call["args"]["reason"])
        result = execute(call["name"], call["args"], approve)
        messages.append({"role": "tool", "name": call["name"], "content": json.dumps(result)})
        if verbose:                                         # OBSERVE
            print(f"    observe: {short(json.dumps(result))}")
    return finish("max_steps")


def part1_the_loop():
    print("######## PART 1 -- What an agent is: an LLM in a loop ########\n")
    print("  | Approach       | Who picks the next step | Can act? |")
    print("  |----------------|-------------------------|----------|")
    print("  | single call    | nobody (one shot)       | no       |")
    print("  | fixed workflow | your code               | yes      |")
    print("  | agent          | the model, every turn   | yes      |\n")
    reset()
    task = task_for("Sam Lee")
    print(f"  TASK: {task}\n")
    r = run_agent(RefundModel(), task, verbose=True)
    print(f"  {r['calls']} LLM calls, {len(r['messages'])} messages, {r['tok_in']} input tokens, "
          f"ledger={LEDGER}")
    print("  Note the context grows every step: the whole history is resent (lesson 03).\n")


# ============================================================================
# PART 2: Stopping conditions
# ============================================================================
#   ┌──────── each turn, BEFORE running the tool ────────┐
#   │ final answer?        ✓ stop (the happy path)       │
#   │ step >= max_steps?   ✗ stop                        │
#   │ tokens >= budget?    ✗ stop                        │
#   │ same call N+1 times? ✗ stop (stuck in a loop)      │
#   │ escalate tool?       ▶ stop, hand to a human       │
#   └────────────────────────────────────────────────────┘

class WanderingModel:
    """Never finds what it needs and keeps rephrasing -- no repeats, no end."""

    def reply(self, messages):
        n = sum(m["role"] == "tool" for m in messages) + 1
        return act(f"Nothing yet, try phrasing #{n}.", "search_kb", {"query": f"refund rules variant {n}"})


class LoopingModel:
    """Calls the exact same tool with the exact same args forever."""

    def reply(self, messages):
        return act("Let me check the orders again.", "get_orders", {"customer_id": "C-101"})


def part2_stopping():
    print("######## PART 2 -- Stopping conditions ########\n")
    runs = [
        ("normal task (Sam, $34.50)", RefundModel(), task_for("Sam Lee"), {}),
        ("policy limit (Ana, $120)", RefundModel(), task_for("Ana Ruiz"), {}),
        ("wanders, max_steps=5", WanderingModel(), "What is the refund rule?", {"max_steps": 5}),
        ("wanders, budget=2000 tok", WanderingModel(), "What is the refund rule?",
         {"max_steps": 100, "max_tokens": 2000}),
        ("same call over and over", LoopingModel(), task_for("Sam Lee"), {"max_steps": 20}),
    ]
    print(f"  {'scenario':<28} {'stop reason':<16} {'calls':>5} {'tokens':>7} {'cost $':>9}")
    for label, model, task, kw in runs:
        reset()
        r = run_agent(model, task, **kw)
        print(f"  {label:<28} {r['stop']:<16} {r['calls']:>5} {r['tok_in'] + r['tok_out']:>7} {r['cost']:>9.5f}")
    print("\n  Without a cap, the wandering agent would run (and bill) forever. A real")
    print("  agent should tell the user WHY it stopped, not fail silently.\n")


# ============================================================================
# PART 3: ReAct vs plan-then-execute
# ============================================================================
#   ReAct                                plan-then-execute
#   ┌─────────┐                          ┌─────────┐ whole plan ┌──────────┐
#   │ thought │◀─ observation ─┐         │ planner │──────────▶│ executor │
#   └────┬────┘                │         │ (1 LLM) │           │ (code)   │
#        ▼ action ──▶ tool ────┘         └─────────┘           └────┬─────┘
#   1 LLM call per step, adapts          few LLM calls, can't adapt ▼ results

PLAN_TEMPLATE = [
    {"tool": "find_customer", "args": {"name": "{name}"}},
    {"tool": "get_orders", "args": {"customer_id": "$1.customer_id"}},
    {"tool": "refund_order", "args": {"order_id": "$2.newest.order_id", "amount": "$2.newest.total"},
     "if": "$2.newest.total < 50", "else": "escalate_to_human"},
]


def resolve(ref, results):
    if not (isinstance(ref, str) and ref.startswith("$")):
        return ref
    head, *path = ref[1:].split(".")
    val = results[int(head) - 1]
    for p in path:
        val = max(val["orders"], key=lambda o: o["date"]) if p == "newest" else val[p]
    return val


def execute_plan(plan):
    results = []
    for i, step in enumerate(plan, 1):
        try:
            if "if" in step:
                lhs, rhs = step["if"].split(" < ")
                if not resolve(lhs, results) < float(rhs):
                    results.append({"escalated": True})
                    continue
            args = {k: resolve(v, results) for k, v in step["args"].items()}
        except (KeyError, ValueError, IndexError) as e:
            return results, f"plan broke at step {i} ({type(e).__name__})"
        res = execute(step["tool"], args)
        results.append(res)
        if "error" in res:
            return results, f"plan broke at step {i} ({res['error'].split(':')[0]})"
    return results, "ok"


def plan_and_execute(name):
    task = task_for(name)
    plan = json.loads(json.dumps(PLAN_TEMPLATE).replace("{name}", name))
    calls = [(est_tokens(SYSTEM + task) + TOOLS_TOKENS, est_tokens(json.dumps(plan)))]    # planner
    results, status = execute_plan(plan)
    summary = f"status={status}, results={json.dumps(results)}"
    calls.append((est_tokens(task + summary), est_tokens("Refunded ORD-7 ($34.50).")))  # summarizer
    return plan, results, status, calls


def part3_react_vs_plan():
    print("######## PART 3 -- ReAct vs plan-then-execute ########\n")
    reset()
    r = run_agent(RefundModel(), task_for("Sam Lee"))
    print("  ReAct trace (Thought / Action / Observation):")
    for m in r["messages"][2:]:
        if m["role"] == "assistant":
            print(f"    Thought: {m['thought']}")
            if "tool_call" in m:
                print(f"    Action : {m['tool_call']['name']}({json.dumps(m['tool_call']['args'])})")
            else:
                print(f"    Answer : {m['content']}")
        else:
            print(f"    Observe: {short(m['content'], 60)}")
    reset()
    plan, results, status, calls = plan_and_execute("Sam Lee")
    print("\n  Plan-then-execute: ONE planner call writes the whole plan:")
    for i, step in enumerate(plan, 1):
        print(f"    {i}. {step['tool']}({json.dumps(step['args'])})")
        if "if" in step:
            print(f"       only if {step['if']}, else {step['else']}")
    print(f"    executor (plain code) -> {status}; refunds={LEDGER}")
    plan_tok = sum(a + b for a, b in calls)
    print(f"\n  {'approach':<20} {'LLM calls':>9} {'tokens':>7}")
    print(f"  {'ReAct':<20} {r['calls']:>9} {r['tok_in'] + r['tok_out']:>7}")
    print(f"  {'plan-then-execute':<20} {len(calls):>9} {plan_tok:>7}")
    reset()
    _, _, status, _ = plan_and_execute("Sam Le")
    r2 = run_agent(RefundModel(), task_for("Sam Le"))
    print("\n  Same two approaches, customer name misspelled ('Sam Le'):")
    print(f"    plan-then-execute: {status} -> needs a NEW planner call")
    print(f"    ReAct            : read the error, answered: {r2['answer']!r}")
    print("  Plan when the steps are predictable; ReAct when results change the plan.\n")


# ============================================================================
# PART 4: Workflows vs agents -- the five common patterns
# ============================================================================
#  chaining   ┌───┐  ┌────┐  ┌───┐    routing   ┌────────┐ ┌▶ billing
#             │ 1 │─▶│gate│─▶│ 2 │              │classify│─┼▶ tech
#             └───┘  └────┘  └───┘              └────────┘ └▶ general
#  parallel   ┌▶ worker ─┐            orch-     ┌──────┐ ┌▶ worker ─┐
#  (sections  ┼▶ worker ─┼▶ combine   workers   │ orch │─┼▶ worker ─┼▶ merge
#   or votes) └▶ worker ─┘            (picks)   └──────┘ └▶ worker ─┘
#  evaluator-    ┌──────────┐ draft ┌───────────┐
#  optimizer     │generator │──────▶│ evaluator │── pass ✓ ──▶ done
#                └──────────┘◀──────└───────────┘
#                         feedback ✗

CALLS: Counter[str] = Counter()


def llm(kind, fn, *args):
    """Every fake LLM call goes through here so we can count them."""
    CALLS[kind] += 1
    return fn(*args)


def demo_chaining():
    outline = llm("chain", lambda p: ["light", "waterproof", "2-person"], "TrailLite tent")
    draft = llm("chain", lambda o: f"TrailLite: a {', '.join(o)} tent for weekend trips.", outline)
    gate = len(draft.split()) <= 15                          # code check between steps
    final_txt = llm("chain", lambda d: d.replace("TrailLite", "TRAILLITE"), draft) if gate else draft
    print(f"    chaining     : outline={outline} -> gate(<=15 words)={gate}")
    print(f"                   -> {final_txt!r}")


def demo_routing():
    routes = {"billing": ("refund", "charge", "invoice"), "tech": ("error", "crash", "login")}
    classify = lambda t: next((k for k, ws in routes.items() if any(w in t.lower() for w in ws)), "general")
    for t in ("I was charged twice", "App crashes on login", "Do you ship to Peru?"):
        route = llm("route", classify, t)
        llm("route", lambda x: x, f"[{route} prompt] {t}")
        print(f"    routing      : {t!r:<24} -> {route} handler")


def demo_parallel():
    code = "def pay(x): eval(x)\n"
    checks = {"security": lambda c: "eval" not in c, "style": lambda c: "(x)" not in c,
              "tests": lambda c: "assert" in c}
    verdicts = {name: llm("parallel", fn, code) for name, fn in checks.items()}
    print(f"    sectioning   : 3 reviewers at once, pass? -> {verdicts}")
    rng, n = random.Random(7), 500
    single = sum(rng.random() < 0.7 for _ in range(n))
    voted = sum(sum(rng.random() < 0.7 for _ in range(5)) >= 3 for _ in range(n))
    print(f"    voting       : one 70%-accurate judge {single / n:.0%} -> majority of 5: {voted / n:.0%}"
          f"  ({n} items, 5x the calls)")


def demo_orchestrator():
    repo = {"api.py": "get_user(id)", "db.py": "def get_user(id):", "ui.py": "render()", "README": "docs"}
    todo = llm("orch", lambda r: [f for f, src in r.items() if "get_user" in src], repo)   # decided at runtime
    done = [llm("orch", lambda f: f"{f}: renamed", f) for f in todo]
    print(f"    orchestrator : request 'rename get_user' -> chose {len(todo)} of {len(repo)} files -> {done}")


def demo_evaluator():
    draft, rounds = "The best tent ever made for every single hiker on earth!", 0
    fixes = {"remove '!'": lambda d: d.replace("!", ""), "max 8 words": lambda d: " ".join(d.split()[:8])}
    while True:
        rounds += 1
        problems = llm("eval", lambda d: [k for k, f in fixes.items() if f(d) != d], draft)
        print(f"    evaluator    : round {rounds}: {draft!r} -> {problems or 'PASS'}")
        if not problems:
            break
        draft = llm("eval", fixes[problems[0]], draft)       # generator fixes one issue per round


def part4_patterns():
    print("######## PART 4 -- Workflows vs agents: five patterns ########\n")
    CALLS.clear()
    for demo in (demo_chaining, demo_routing, demo_parallel, demo_orchestrator, demo_evaluator):
        demo()
    print(f"\n  LLM calls per pattern: {dict(CALLS)}\n")
    print("  | Use a WORKFLOW (code picks steps)    | Use an AGENT (model picks steps)        |")
    print("  |--------------------------------------|-----------------------------------------|")
    print("  | steps known in advance               | steps depend on what tools return       |")
    print("  | need predictable cost and latency    | open-ended tasks, unknown # of steps    |")
    print("  | easy to test each step               | you can afford retries and evals        |")
    print("  | high-stakes, auditable pipelines     | a human or sandbox limits the damage    |")
    print("  Start with the simplest thing (one call), add a workflow, reach for an")
    print("  agent only when the task truly needs the model to choose.\n")


# ============================================================================
# PART 5: Memory
# ============================================================================
#   ┌────────────── context window (one call) ──────────────┐
#   │ system │ retrieved facts │ scratchpad │ messages ...  │
#   └────────────────▲──────────────────────────────────────┘
#                    │ search(query) -> top-k facts
#   ┌────────────────┴────────┐
#   │ long-term store (DB)    │ ◀── save(fact) during / after sessions
#   └─────────────────────────┘

FACTS = [f"Customer {n} prefers delivery slot {k}." for n in ("Ana", "Bo", "Cy", "Di") for k in range(10)] + [
    "Sam Lee wants refund updates by email, never by phone.",
    "Sam Lee had a refund in March for a damaged tent.",
]


def retrieve(query, facts, k=2):
    words = lambda s: set(re.findall(r"[a-z]{3,}", s.lower()))
    return sorted(facts, key=lambda f: -len(words(query) & words(f)))[:k]


def part5_memory():
    print("######## PART 5 -- Memory ########\n")
    reset()
    r = run_agent(RefundModel(), task_for("Sam Lee"))
    print(f"  SHORT-TERM = the message list. Context per call in part 1: {r['context']} tokens")
    results = [f"result {i}: " + "log line " * 130 for i in range(12)]
    notes = [f"step {i}: checked source {i}, nothing relevant" for i in range(12)]
    full = sum(est_tokens(x) for x in results)
    compact = sum(est_tokens(x) for x in notes) + sum(est_tokens(x) for x in results[-2:])
    print("  SCRATCHPAD = the agent writes short notes, old raw tool results are dropped.")
    print(f"    after 12 steps: keep every raw result {full} tok vs notes + last 2 results {compact} tok")
    query = "How should we contact Sam Lee about this refund?"
    hits = retrieve(query, FACTS)
    print(f"  LONG-TERM = facts stored OUTSIDE the context, searched per task ({len(FACTS)} stored).")
    print(f"    query: {query!r}")
    for h in hits:
        print(f"      retrieved: {h}")
    print(f"    stuff all facts: {est_tokens(' '.join(FACTS))} tok vs top-2: {est_tokens(' '.join(hits))} tok")
    print("  These are lesson 04's WRITE / SELECT / COMPRESS strategies applied to agents.\n")


# ============================================================================
# PART 6: Multi-agent -- subagents with isolated contexts
# ============================================================================
#   one agent: docs pile up          orchestrator + subagents
#   ┌───────────────────────┐        ┌──────────────┐
#   │ doc A │ doc B │ doc C │        │ orchestrator │ sees 3 one-line summaries
#   └───────────────────────┘        └──┬───┬───┬───┘
#   resent on every later call          ▼   ▼   ▼   summary ▲ back up
#                                   ┌─────┐┌─────┐┌─────┐
#                                   │sub A││sub B││sub C│ fresh context each,
#                                   │docA ││docB ││docC │ reads ONE doc
#                                   └─────┘└─────┘└─────┘

PRODUCTS = {"tent": "30 days, unused", "stove": "14 days, receipt needed", "boots": "60 days, any condition"}


def product_doc(p):
    lines = [f"{p} spec line {i}: weight, size, colour, materials and care notes." for i in range(80)]
    lines.insert(40, f"Returns: {p} can be returned within {PRODUCTS[p]}.")
    return "\n".join(lines)


def call_cost(messages):
    return est_tokens(json.dumps(messages))


def part6_subagents():
    print("######## PART 6 -- Subagents: isolated contexts ########\n")
    task = "Summarise the return policy of tent, stove and boots."
    # A) one agent reads every doc itself
    msgs, single = [{"role": "user", "content": task}], []
    for p in PRODUCTS:
        single.append(call_cost(msgs))
        msgs.append({"role": "tool", "content": product_doc(p)})
    single.append(call_cost(msgs))
    # B) orchestrator delegates; each subagent has a FRESH context, returns one line
    orch, orch_calls, sub_calls = [{"role": "user", "content": task}], [], []
    for p in PRODUCTS:
        orch_calls.append(call_cost(orch))
        sub = [{"role": "user", "content": f"Find the return policy for {p}."}]
        sub_calls.append(call_cost(sub))
        sub.append({"role": "tool", "content": product_doc(p)})
        sub_calls.append(call_cost(sub))
        summary = re.search(r"Returns: (.+)", product_doc(p)).group(1)     # subagent's answer
        orch.append({"role": "tool", "content": summary})
    orch_calls.append(call_cost(orch))
    print(f"  {'':<26} {'peak context':>12} {'total input tok':>16} {'LLM calls':>10}")
    print(f"  {'A) one agent':<26} {max(single):>12} {sum(single):>16} {len(single):>10}")
    print(f"  {'B) orchestrator only':<26} {max(orch_calls):>12} {sum(orch_calls):>16} {len(orch_calls):>10}")
    print(f"  {'   + its 3 subagents':<26} {max(sub_calls):>12} {sum(sub_calls):>16} {len(sub_calls):>10}")
    total_b = sum(orch_calls) + sum(sub_calls)
    print(f"\n  Orchestrator context: {max(orch_calls)} vs {max(single)} tokens "
          f"({max(single) / max(orch_calls):.0f}x smaller). Total B = {total_b} vs A = {sum(single)}.")
    print("  What it received from the subagents:")
    for m in orch[1:]:
        print(f"    - {m['content']}")
    print("  Subagents can run in parallel and keep noise out of the parent. The cost:")
    print("  more calls, and the parent only knows what the summary says.\n")


# ============================================================================
# PART 7: Errors and recovery
# ============================================================================
#   tool error ──▶ result {"error": "how to fix"} ──▶ model retries ✓
#   transient 503 ──▶ YOUR code retries with backoff (model never sees it)
#   risky action ──▶ ┌────────────────┐ yes ▶ run
#                    │ human approve? │ no  ▶ {"error": "USER_DECLINED"}
#                    └────────────────┘

def with_retries(fn, attempts=3):
    log = []
    for i in range(1, attempts + 1):
        try:
            return fn(), log
        except ConnectionError as e:
            log.append(f"attempt {i}: {e}, wait {0.5 * 2 ** (i - 1)}s")
    return {"error": "UNAVAILABLE after retries"}, log


def part7_errors():
    print("######## PART 7 -- Errors and recovery ########\n")
    print("  a) Bad arguments -> the error text tells the model how to fix it:")
    reset()
    run_agent(RefundModel(sloppy=True), task_for("Sam Lee"), verbose=True)

    failures = iter([ConnectionError("503"), ConnectionError("503")])

    def flaky_orders():
        err = next(failures, None)
        if err:
            raise err
        return get_orders("C-101")

    result, log = with_retries(flaky_orders)
    print("  b) Transient failures are retried by CODE, not by the model:")
    for line in log:
        print(f"    {line}")
    print(f"    attempt {len(log) + 1}: ok -> {short(json.dumps(result), 50)}\n")

    print("  c) Human-in-the-loop for risky tools (lesson 07 part 8):")
    for decision in (True, False):
        reset()

        def human(name, args, d=decision):
            print(f"    [approve?] {name}({json.dumps(args)}) -> {'yes' if d else 'no'}")
            return d
        r = run_agent(RefundModel(), task_for("Sam Lee"), approve=human)
        print(f"    agent says: {r['answer']!r}   ledger={LEDGER}")
    print("\n  d) Loop guards: max_steps + repeated-call detection (part 2), plus a")
    print("     cap on retries per tool. A declined action must NOT be retried.\n")


# ============================================================================
# PART 8: Evaluating agents
# ============================================================================
#   ┌────────┐   ┌──────────────┐   ┌─────────────────┐   ┌────────────────┐
#   │ N tasks│──▶│ run the agent│──▶│ compare outcome │──▶│ success %,     │
#   │ + truth│   │ (fixed seeds)│   │ to ground truth │   │ steps, $/task  │
#   └────────┘   └──────────────┘   └─────────────────┘   └────────────────┘

def make_case(rng, i):
    name = f"{rng.choice(['Ava', 'Ben', 'Cleo', 'Dev', 'Eli'])} Tester{i}"
    orders = [{"order_id": f"ORD-{i}-{k}", "total": round(rng.uniform(10, 120), 2),
               "date": f"2026-{rng.randint(1, 9):02d}-{rng.randint(10, 28)}"}
              for k in range(rng.choice([0, 1, 2, 2, 3, 3]))]
    db = {"customers": {name: f"C-{500 + i}"}, "orders": {f"C-{500 + i}": orders}}
    asked = name[:-1] if rng.random() < 0.1 else name          # 10% misspelled names
    if asked != name:
        truth = ("not_found",)
    elif not orders:
        truth = ("no_orders",)
    else:
        newest = max(orders, key=lambda o: o["date"])
        truth = ("refunded" if newest["total"] < 50 else "escalated", newest["order_id"])
    return db, asked, truth


def outcome(r):
    if r["stop"] == "escalated":
        return ("escalated", r["messages"][-1]["tool_call"]["args"]["order_id"])
    if LEDGER:
        return ("refunded", LEDGER[0][0])
    if r["answer"] and "couldn't find" in r["answer"]:
        return ("not_found",)
    return ("no_orders",) if r["answer"] and "no orders" in r["answer"] else (r["stop"],)


def evaluate(error_rate, n=40):
    rng, stats = random.Random(42), {"ok": 0, "calls": [], "cost": [], "fail": Counter()}
    for i in range(n):
        db, asked, truth = make_case(rng, i)
        reset(db)
        r = run_agent(RefundModel(error_rate=error_rate, seed=1000 + i), task_for(asked))
        got = outcome(r)
        stats["ok"] += got == truth
        if got != truth:
            what = "right action, WRONG order" if got[0] == truth[0] else f"{truth[0]} -> {got[0]}"
            stats["fail"][what] += 1
        stats["calls"].append(r["calls"])
        stats["cost"].append(r["cost"])
    return stats


def part8_eval():
    print("######## PART 8 -- Evaluating agents ########\n")
    n = 40
    print(f"  {n} generated tasks with known right answers (seeded). Two agent versions:")
    print(f"  {'version':<26} {'success':>8} {'avg steps':>10} {'max':>4} {'avg $/task':>11}")
    results = {}
    for label, err in (("v1 (misreads 'last' 25%)", 0.25), ("v2 (better prompt, 5%)", 0.05)):
        s = evaluate(err, n)
        results[label] = s
        print(f"  {label:<26} {s['ok'] / n:>8.0%} {sum(s['calls']) / n:>10.2f} {max(s['calls']):>4} "
              f"{sum(s['cost']) / n:>11.6f}")
    for label, s in results.items():
        print(f"  failures {label[:2]}: {dict(s['fail']) or 'none'}")
    reset()
    print("\n  Grade the OUTCOME (right order refunded?), not the wording. Track steps")
    print("  and cost too: a 'correct' agent that takes 30 steps is a bug.\n")


# ============================================================================
# PART 9: Where frameworks and MCP fit
# ============================================================================
#   ┌──────────────────────────────────────────────────────────────┐
#   │ framework: LangGraph, Agents SDKs, ... (+ MCP servers)       │
#   ├──────────────────────────────────────────────────────────────┤
#   │ agent loop: stop checks, memory, approval   (THIS lesson)    │
#   ├──────────────────────────────────────────────────────────────┤
#   │ tool calling: schema, validate, run         (lesson 07)      │
#   ├──────────────────────────────────────────────────────────────┤
#   │ model API: messages in, text/tool calls out (lessons 01-03)  │
#   └──────────────────────────────────────────────────────────────┘

def part9_frameworks():
    print("######## PART 9 -- Where frameworks and MCP fit ########\n")
    print("""  Layer          What it adds                                  In this repo
  model API      messages -> text or tool calls                lessons 01-03
  tool calling   schemas, validation, errors as results        lesson 07, 08
  agent loop     stopping, memory, approval, subagents         this lesson
  framework      graphs/state, checkpoints, tracing, retries   ../learn-langgraph,
                                                               ../learn-agents
  MCP            a PROTOCOL to plug tool servers into any      ../mcp, ../learn-mcp
                 agent -- it supplies tools, not the loop

  Frameworks package the run_agent() loop above. Learn the loop
  first; then a framework is a convenience, not magic. Build a whole
  agent from scratch in ../learn-mini-claude.
""")


def main():
    part1_the_loop()
    part2_stopping()
    part3_react_vs_plan()
    part4_patterns()
    part5_memory()
    part6_subagents()
    part7_errors()
    part8_eval()
    part9_frameworks()


if __name__ == "__main__":
    main()

    # -- Key takeaway --------------------------------------------------------
    # An agent = LLM + tools + a loop where the model picks the next step.
    #   - The loop is YOUR code: stop reasons, budgets, approval, logging.
    #   - Prefer workflows when the steps are known; agents when they aren't.
    #   - Keep context small: scratchpads, retrieval, subagents.
    #   - Evaluate on many tasks with ground truth: success, steps, cost.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Set max_repeats=0 in part 2. Which scenarios change stop reason?
    # 2. Give RefundModel a 'wrong tool name' slip. What does execute() return?
    # 3. Raise the eval to n=200. Do v1/v2 success rates stay stable?
    # 4. Add a token budget to part 6's single agent. Where does it stop?
