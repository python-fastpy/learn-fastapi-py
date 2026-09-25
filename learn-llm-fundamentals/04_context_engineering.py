"""Lesson 04 -- Context engineering: deciding what the model sees
=================================================================

WHY THIS MATTERS:
  Lessons 01-03 established three facts:
    - the model only knows its training data + what's in the context now
    - the API is stateless, so YOU assemble the context on every call
    - every token of context costs money, latency, and attention

  So the job of an AI engineer is mostly this:

      For every LLM call, put the RIGHT information in the context,
      in the RIGHT form, in the RIGHT order -- and nothing else.

  That's context engineering. "Prompt engineering" (wording the
  instructions well) is one part of it. The rest is plumbing: retrieval,
  memory, history compaction, tool selection, trimming tool output,
  ordering for caching, and isolating noisy sub-tasks.

WHAT YOU'LL LEARN:
  1. The context window as a BUDGET, and what competes for it
  2. Why naive "stuff everything in, truncate" fails -- measured
  3. The four strategies: WRITE, SELECT, COMPRESS, ISOLATE
  4. Ordering: stable prefix first (caching), question last (attention)
  5. How to CHECK a context: does it contain the facts the answer needs?
  6. The failure modes: poisoning, distraction, confusion, clash

Concepts:
  - Context window: max tokens per call (input + output) for a model
  - Token budget: how much of that you allow each component to use
  - Retrieval (RAG): select only the documents relevant to this question
  - Compaction: replace old conversation turns with a short summary
  - Memory: facts stored OUTSIDE the context, re-injected when relevant
  - Prompt caching: providers discount a repeated identical PREFIX

Flow:
      raw material (way over budget)            engineered context (fits)
      ------------------------------            -------------------------
      system rules             ----------keep------> system rules        \\
      12 tool definitions      ---SELECT 3--------> 3 relevant tools      > stable prefix
      long-term memory         ---SELECT----------> 1-2 relevant facts   /  (cacheable)
      10 knowledge-base docs   ---SELECT top-k----> 2 relevant docs      \\
      14-turn chat history     ---COMPRESS--------> summary + last 4      \\
      40-field account JSON    ---COMPRESS--------> 4 relevant fields     / volatile
      the user's question      ----------keep, LAST> the question        /
      noisy sub-task (search)  ---ISOLATE---------> subagent's summary only

PREREQUISITES: Lessons 01-03. Pure Python, no packages, no credentials.

Run:  uv run python 04_context_engineering.py
"""

import json
import math
import re
from dataclasses import dataclass


def est_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


BUDGET = 600          # tokens we allow for INPUT context in this demo
RESERVED_OUTPUT = 300 # keep room for the answer: window = input + output


# ============================================================================
# The raw material -- everything we COULD send
# ============================================================================

SYSTEM = (
    "You are the support assistant for Acme Cloud. Answer only from the "
    "provided documents and account data. If the answer is not there, say so. "
    "Give numbered steps. Prefer the interface the user prefers."
)

QUESTION = ("My deploys to eu-west keep failing with error E403 since I upgraded "
            "to the Pro plan yesterday. What should I do?")

# What a correct answer MUST rely on. We'll check which contexts contain them.
REQUIRED_FACTS = {
    "E403 meaning (from docs)": "missing the region scope",
    "region not enabled (from account)": '"regions_enabled": ["us-east"]',
    "user prefers CLI (from old history)": "CLI over the dashboard",
    "the question itself": "error E403 since I upgraded",
}

TOOLS = {
    name: f"{name}: {desc}"
    for name, desc in [
        ("get_account", "Fetch the user's account, plan, regions and deploy keys."),
        ("list_deploys", "List recent deploys with status and error codes."),
        ("regenerate_deploy_key", "Create a new deploy key with the given scopes."),
        ("enable_region", "Enable a region for the account (Pro plan and above)."),
        ("get_invoice", "Fetch an invoice by id."),
        ("update_payment_method", "Change the card on file."),
        ("list_team_members", "List users in the organisation."),
        ("invite_team_member", "Invite a user by email."),
        ("get_usage_report", "Monthly compute and bandwidth usage."),
        ("create_support_ticket", "Escalate to a human support engineer."),
        ("set_notification_prefs", "Email and Slack notification settings."),
        ("delete_project", "Permanently delete a project and all deploys."),
    ]
}
ALWAYS_ON_TOOLS = {"create_support_ticket"}

KNOWLEDGE_BASE = {
    "errors/E403": "Error E403 on deploy means the deploy key is missing the region scope "
                   "for the target region, or the region is not enabled on the account. "
                   "Fix: enable the region, then regenerate the deploy key with that region scope.",
    "errors/E500": "Error E500 is an internal error. Retry after a few minutes; if it persists, "
                   "open a support ticket with the deploy id.",
    "plans/pro": "The Pro plan includes up to 5 regions, 10 team members and priority support. "
                 "Regions are not enabled automatically after an upgrade.",
    "plans/free": "The Free plan includes 1 region (us-east) and 1 team member.",
    "cli/keys": "CLI: `acme keys create --scope region:<name>` creates a scoped deploy key. "
                "`acme regions enable <name>` enables a region.",
    "dashboard/keys": "Dashboard: Settings > Keys > New key, then tick the region scopes you need.",
    "billing/invoices": "Invoices are issued on the 1st of each month and emailed to the owner.",
    "billing/refunds": "Refunds are available within 14 days of an upgrade on request.",
    "team/sso": "SSO via SAML is available on the Enterprise plan only.",
    "status/incidents": "Current incidents are listed at status.acme.example. None are active.",
}

HISTORY = [  # (role, text)  oldest first -- a long earlier conversation
    ("user", "Hi, I'm setting up Acme for my team at Globex."),
    ("assistant", "Welcome! What would you like to set up first?"),
    ("user", "Just so you know, I always use the terminal -- I prefer the CLI over the dashboard."),
    ("assistant", "Noted, I'll give CLI instructions."),
    ("user", "How do invoices work?"),
    ("assistant", "Invoices are issued on the 1st of each month and emailed to the owner."),
    ("user", "Can I get SSO?"),
    ("assistant", "SSO via SAML is on the Enterprise plan only."),
    ("user", "OK. How many team members on Pro?"),
    ("assistant", "Pro includes up to 10 team members."),
    ("user", "Great, I upgraded to Pro."),
    ("assistant", "Thanks for upgrading! Anything else?"),
    ("user", "Not right now, thanks."),
    ("assistant", "You're welcome."),
]

ACCOUNT = {  # what get_account returned -- 40 fields, 4 matter here
    "id": "acct_91f2", "org": "Globex", "plan": "pro", "plan_changed_at": "yesterday",
    "regions_enabled": ["us-east"], "deploy_key_scopes": ["region:us-east"],
    "last_deploy_error": "E403", "last_deploy_region": "eu-west",
    **{f"setting_{i}": f"value_{i}_{'x' * 18}" for i in range(32)},
}

MEMORY = {  # long-term memory from PREVIOUS sessions (WRITE strategy output)
    "timezone": "User is in CET.",
    "company": "User's company is Globex.",
    "tone": "User likes short answers.",
}


# ============================================================================
# PART 1: Naive context -- stuff everything, then truncate
# ============================================================================

def render_history(turns) -> str:
    return "\n".join(f"{r}: {t}" for r, t in turns)


def naive_context() -> str:
    return "\n\n".join([
        "SYSTEM:\n" + SYSTEM,
        "TOOLS:\n" + "\n".join(TOOLS.values()),
        "MEMORY:\n" + "\n".join(MEMORY.values()),
        "DOCS:\n" + "\n".join(f"[{k}] {v}" for k, v in KNOWLEDGE_BASE.items()),
        "HISTORY:\n" + render_history(HISTORY),
        "ACCOUNT:\n" + json.dumps(ACCOUNT),
        "USER:\n" + QUESTION,
    ])


def check_facts(context: str) -> dict[str, bool]:
    return {name: needle in context for name, needle in REQUIRED_FACTS.items()}


def report(label: str, context: str):
    facts = check_facts(context)
    ok = sum(facts.values())
    print(f"  {label}")
    print(f"    size: {est_tokens(context):>5} tokens (budget {BUDGET})   "
          f"required facts present: {ok}/{len(facts)}")
    for name, present in facts.items():
        print(f"      [{'x' if present else ' '}] {name}")
    print()


def part1_naive():
    print("######## PART 1 -- Naive: include everything ########\n")
    full = naive_context()
    report("A) everything, no limit", full)

    limit = BUDGET * 4   # chars
    report("B) truncate to budget -- keep the START", full[:limit])
    report("C) truncate to budget -- keep the END", full[-limit:])
    print("  A has every fact but is far over budget (and pays for 10 docs,")
    print("  12 tools and 36 junk fields to answer one question).")
    print("  B cuts off the question and the account data. C cuts off the")
    print("  system rules and the docs. Blind truncation always loses")
    print("  SOMETHING -- you have to choose what goes in, not just how much.\n")


# ============================================================================
# PART 2: Engineered context -- the four strategies
# ============================================================================

STOPWORDS = set("a an the to my i is are of on in and or for with since what should do "
                "keep yesterday".split())


def keywords(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9\-]+", text.lower()) if w not in STOPWORDS}


def relevance(query: str, text: str) -> int:
    """Keyword overlap. Real systems use embeddings (learn-ai-advanced 01)
    plus a reranker -- same role: score each candidate against the query."""
    return len(keywords(query) & keywords(text))


# ---- SELECT: only what this question needs ---------------------------------

def select_docs(query: str, k: int = 2) -> list[tuple[str, str]]:
    ranked = sorted(KNOWLEDGE_BASE.items(), key=lambda kv: -relevance(query, kv[1]))
    return ranked[:k]


def select_tools(query: str, k: int = 3) -> list[str]:
    ranked = sorted(TOOLS, key=lambda n: -relevance(query + " key deploy region", TOOLS[n]))
    return sorted(set(ranked[:k]) | ALWAYS_ON_TOOLS)


def select_memory(query: str) -> list[str]:
    # Keep memories that touch the query, plus ones that always apply (tone).
    return [v for k, v in MEMORY.items() if k == "tone" or relevance(query, v) > 0]


# ---- COMPRESS: same information, fewer tokens ------------------------------

def compact_history(turns, keep_last: int = 4) -> str:
    """Old turns -> a short summary; recent turns kept verbatim.

    In production the summary is written by an LLM call (often a cheaper
    model), or incrementally as the chat goes. Here we keep the turns a
    summarizer should preserve: stated preferences and decisions.
    """
    old, recent = turns[:-keep_last], turns[-keep_last:]
    durable = [t for r, t in old if r == "user" and
               any(w in t.lower() for w in ("prefer", "always", "upgraded", "team at"))]
    summary = "Earlier in this conversation: " + " ".join(
        s.replace("I always use the terminal -- I prefer", "user prefers")
         .replace("Just so you know, ", "") for s in durable)
    return summary + "\n" + render_history(recent)


def trim_tool_result(data: dict, fields: list[str]) -> str:
    """Tool output is often the biggest context hog. Keep what matters."""
    return json.dumps({k: data[k] for k in fields if k in data})


# ---- ORDER: stable first (cache), question last (attention) ----------------

@dataclass
class Section:
    name: str
    text: str
    stable: bool    # identical across requests -> belongs in the cached prefix
    priority: int   # lower = drop first when over budget


def engineered_sections(query: str) -> list[Section]:
    docs = select_docs(query)
    return [
        Section("system", "SYSTEM:\n" + SYSTEM, stable=True, priority=100),
        Section("tools", "TOOLS:\n" + "\n".join(TOOLS[t] for t in select_tools(query)),
                stable=False, priority=90),
        Section("memory", "MEMORY:\n" + "\n".join(select_memory(query)), stable=False, priority=40),
        Section("docs", "DOCS:\n" + "\n".join(f"[{k}] {v}" for k, v in docs),
                stable=False, priority=80),
        Section("history", "HISTORY:\n" + compact_history(HISTORY), stable=False, priority=60),
        Section("account", "ACCOUNT:\n" + trim_tool_result(
            ACCOUNT, ["plan", "regions_enabled", "deploy_key_scopes", "last_deploy_region"]),
            stable=False, priority=85),
        # The question goes LAST: models attend most to the start and end of
        # long contexts ("lost in the middle"), and ending on the task keeps
        # the model focused on answering it.
        Section("question", "USER:\n" + query, stable=False, priority=100),
    ]


def fit_to_budget(sections: list[Section], budget: int) -> tuple[list[Section], list[str]]:
    """Drop whole low-priority sections until we fit -- never cut mid-section."""
    kept, dropped = list(sections), []
    while sum(est_tokens(s.text) for s in kept) > budget:
        victim = min((s for s in kept if s.priority < 100), key=lambda s: s.priority)
        kept.remove(victim)
        dropped.append(victim.name)
    return kept, dropped


def part2_engineered():
    print("######## PART 2 -- Engineered: select, compress, order ########\n")
    raw_sizes = {
        "system": est_tokens(SYSTEM),
        "tools": est_tokens("\n".join(TOOLS.values())),
        "memory": est_tokens("\n".join(MEMORY.values())),
        "docs": est_tokens("\n".join(KNOWLEDGE_BASE.values())),
        "history": est_tokens(render_history(HISTORY)),
        "account": est_tokens(json.dumps(ACCOUNT)),
        "question": est_tokens(QUESTION),
    }
    actions = {
        "system": "keep (stable)",
        "tools": f"SELECT {len(select_tools(QUESTION))} of {len(TOOLS)}",
        "memory": f"SELECT {len(select_memory(QUESTION))} of {len(MEMORY)}",
        "docs": f"SELECT top-2 of {len(KNOWLEDGE_BASE)}: "
                + ", ".join(k for k, _ in select_docs(QUESTION)),
        "history": "COMPRESS: summary + last 4 turns",
        "account": "COMPRESS: 4 of 40 fields",
        "question": "keep, placed LAST",
    }
    sections, dropped = fit_to_budget(engineered_sections(QUESTION), BUDGET)
    print(f"  {'section':<10} {'raw':>6} -> {'final':>5}   action")
    print(f"  {'-' * 10} {'-' * 6}    {'-' * 5}   {'-' * 40}")
    for s in sections:
        print(f"  {s.name:<10} {raw_sizes[s.name]:>6} -> {est_tokens(s.text):>5}   {actions[s.name]}")
    total_raw = sum(raw_sizes.values())
    context = "\n\n".join(s.text for s in sections)
    print(f"  {'TOTAL':<10} {total_raw:>6} -> {est_tokens(context):>5}   "
          f"({est_tokens(context) / total_raw:.0%} of the raw size)"
          + (f"   dropped: {dropped}" if dropped else ""))
    print()
    report("D) engineered context", context)
    print("  All the facts, a fraction of the tokens. The two strategies not")
    print("  shown in this table:")
    print("    WRITE   -- MEMORY came from facts saved in PREVIOUS sessions, outside")
    print("               any context window (a DB/file), re-injected when relevant.")
    print("    ISOLATE -- if answering needed a big search (logs, 50 files), a")
    print("               subagent would do it in its own context and return only")
    print("               a summary (learn-mini-claude lesson 06).\n")
    return context


# ============================================================================
# PART 3: Ordering for prompt caching
# ============================================================================
# Providers cache the longest IDENTICAL PREFIX between requests and bill
# it at a large discount. One changed byte early on invalidates
# everything after it.

def common_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def part3_caching():
    print("######## PART 3 -- Order for caching: stable first ########\n")
    requests = [("09:00:01", QUESTION), ("09:02:17", "Which CLI command enables eu-west?"),
                ("09:05:40", "And how do I regenerate the key?")]

    all_tools = "TOOLS:\n" + "\n".join(TOOLS.values())

    def bad(ts, q):   # volatile content first
        return f"Current time: {ts}\nUSER:\n{q}\n\nSYSTEM:\n{SYSTEM}\n\n{all_tools}"

    def good(ts, q):  # stable content first, volatile last
        return f"SYSTEM:\n{SYSTEM}\n\n{all_tools}\n\nCurrent time: {ts}\nUSER:\n{q}"

    for label, build in [("volatile FIRST (timestamp, question, then rules)", bad),
                         ("stable FIRST  (rules, tools, then timestamp, question)", good)]:
        ctxs = [build(ts, q) for ts, q in requests]
        shares = [common_prefix(ctxs[i], ctxs[i + 1]) / len(ctxs[i + 1]) for i in range(2)]
        print(f"  {label}")
        print(f"    cacheable share of requests 2 and 3: "
              f"{shares[0]:.0%}, {shares[1]:.0%}\n")
    print("  Same content, same tokens -- only the order changed. Rules of thumb:")
    print("   - system prompt and tool definitions first, byte-for-byte identical")
    print("     every call (no timestamps, no user names, sorted JSON keys)")
    print("   - per-request material (retrieved docs, question, time) at the end")
    print("   - trade-off: per-question tool SELECTION (part 2) changes the tool")
    print("     block and breaks the cache. With a few tools, send them all and")
    print("     cache; with hundreds, select (or use provider tool search).\n")


# ============================================================================
# PART 4: How contexts go wrong
# ============================================================================

def part4_failure_modes():
    print("######## PART 4 -- Context failure modes ########\n")
    rows = [
        ("Poisoning", "A wrong fact (a hallucination, a bad tool result, an injected "
         "instruction) enters the context and gets reused turn after turn.",
         "Validate tool output; don't persist unverified model claims into memory; "
         "treat retrieved text as data (learn-ai-advanced 04)."),
        ("Distraction", "So much material that the model follows the noise, or copies "
         "old history instead of reasoning about the new question.",
         "SELECT and COMPRESS. More context is not better context."),
        ("Confusion", "Too many similar tools/docs; the model picks the wrong one.",
         "Fewer, clearly named tools with distinct descriptions; tool selection."),
        ("Clash", "Two parts of the context disagree (old doc vs new doc, system "
         "rule vs user instruction).",
         "Date and source every doc; remove superseded info; state precedence "
         "in the system prompt."),
        ("Truncation", "Something required fell off the end -- or the ANSWER was cut "
         "off by max_tokens.",
         "Budget by section (part 2); reserve output tokens; check stop_reason."),
    ]
    for name, what, fix in rows:
        print(f"  {name}")
        print(f"    what: {what}")
        print(f"    fix : {fix}\n")


# ============================================================================
# PART 5: The checklist
# ============================================================================

def part5_checklist():
    print("######## PART 5 -- Context engineering checklist ########\n")
    print("""  Before every LLM call in your app, you should be able to answer:

    [ ] What does the model need to answer THIS request? (list the facts)
    [ ] Where does each fact come from? (system, retrieval, memory, tool, history)
    [ ] Is anything in the context NOT needed? Remove it.
    [ ] Is each component within its budget, with output tokens reserved?
    [ ] Is the stable part first and byte-identical across calls? (caching)
    [ ] Is the task / question at the end?
    [ ] Is untrusted content (docs, tool output, web pages) marked as data?
    [ ] For long sessions: what gets summarized, and what gets saved to memory?
    [ ] For big sub-tasks: should a subagent do this in its own context?
    [ ] Can you LOG the exact context sent, so you can debug a bad answer?
        (learn-ai-advanced 03 -- most 'model bugs' are context bugs)
""")


def main():
    print(f"Question: {QUESTION}\n")
    part1_naive()
    part2_engineered()
    part3_caching()
    part4_failure_modes()
    part5_checklist()


if __name__ == "__main__":
    main()

    # -- Key takeaway --------------------------------------------------------
    # A model can only be as good as its context. The four strategies:
    #   WRITE    -- save facts outside the context (memory, notes, files)
    #   SELECT   -- pull in only what this call needs (RAG, tool selection)
    #   COMPRESS -- same info, fewer tokens (summaries, trimmed tool output)
    #   ISOLATE  -- push noisy sub-tasks into separate contexts (subagents)
    # Then ORDER it: stable first for caching, task last for attention.
    # And VERIFY it: check the facts the answer needs are actually present.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Set BUDGET = 300 and re-run. Which section does fit_to_budget drop?
    #    Is that the right one? Change priorities until the facts survive.
    # 2. Set keep_last=12 in compact_history -- nothing is summarized. How
    #    many tokens did compaction save?
    # 3. Add a stale doc "errors/E403-old": "E403 means your card was
    #    declined." Does select_docs pick it? That's a CLASH -- fix it by
    #    adding a date/version to each doc and preferring the newest.
    # 4. Replace relevance() with embeddings from learn-ai-advanced 01.
