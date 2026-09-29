"""Lesson 09 -- Human-in-the-Loop with interrupt()
==================================================

Some work should not finish unsupervised: an AI-drafted greeting wants an
editor's eye before it is sent. `interrupt()` stops the graph mid-node, saves
everything, and hands a payload to the caller. Later, `Command(resume=...)`
continues the run with the human's answer.

  START ──► draft_greeting ──► human_review ──┬── "approve" ──► END
                  ▲                           │
                  └────────── "revise" ───────┘   loop: draft again

  what one pause actually looks like:

    app.invoke({...})                  app.invoke(Command(resume="approve"))
      │                                  │
      draft_greeting   (LLM call)        human_review RE-ENTERED at line 1
      │                                  │    every line above interrupt()
      human_review                       │    RUNS A SECOND TIME
      │  interrupt({draft, prompt}) ──┐  │
      │                               │  │    interrupt() now RETURNS
      ▼                               │  │    "approve" instead of pausing
    invoke RETURNS, carrying           │  ▼
    "__interrupt__"                    │  route_after_review -> END
    nothing is blocked ────────────────┘

  1. interrupt(payload)  saves state, hands `payload` to the caller, and
                         invoke() RETURNS. No thread is parked.
  2. CHECKPOINTER        required. The pause has to write state somewhere;
                         without one, interrupt() cannot work.
  3. thread_id           the resume handle, same as lesson 08.
  4. Command(resume=v)   re-runs the interrupted node, and this time
                         interrupt() evaluates to `v`.
  5. RE-ENTRY            the node restarts from its FIRST line. It does not
                         continue below interrupt(). So anything above the
                         interrupt runs twice -- keep it free of side effects
                         (no emails, no inserts, no charges).
  6. THE LOOP            a conditional edge decides: back to drafting on
                         "revise", END on "approve".

  Point 5 is the one that bites. This file counts its own re-entries and
  prints the total, so you can see it rather than take my word for it.

** Requires .env with orchestrator credentials **

Run:  uv run python 09_human_in_the_loop.py

Maps to: langgraph_mcp_orchestrator.py -> interrupt() + resume;
dynamodb_checkpointer.py -> where the pause is stored;
the skills interrupt component -> renders the payload as a review screen
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command, interrupt

from llm_helper import get_llm

llm = get_llm(model="gpt-4o")

ENTRIES: list[str] = []          # proof for point 5, printed at the end


def draft_greeting(state: MessagesState) -> dict:
    """Runs for the first draft AND for every revision."""
    return {"messages": [llm.invoke(state["messages"])]}


def human_review(state: MessagesState) -> dict:
    draft = state["messages"][-1].content

    # 5. This line is ABOVE the interrupt, so it runs again on every resume.
    ENTRIES.append(draft[:30])

    decision = interrupt({                       # 1. pause, hand this to the caller
        "type": "greeting_review",               #    production sends an EventType
        "draft": draft,                          #    so the UI picks a screen
        "prompt": "Approve this greeting? (approve / revise: <feedback>)",
    })

    # 4. Reached only once a resume value has arrived.
    if decision.startswith("approve"):
        return {"messages": [AIMessage(content=f"APPROVED: {draft}")]}

    feedback = decision.replace("revise:", "").strip()
    return {"messages": [HumanMessage(content=f"Please revise it. Feedback: {feedback}")]}


def route_after_review(state: MessagesState) -> str:
    last = state["messages"][-1]
    approved = isinstance(last, AIMessage) and last.content.startswith("APPROVED")
    return END if approved else "draft_greeting"      # 6. the loop


graph = StateGraph(MessagesState)
graph.add_node("draft_greeting", draft_greeting)
graph.add_node("human_review", human_review)
graph.add_edge(START, "draft_greeting")
graph.add_edge("draft_greeting", "human_review")
graph.add_conditional_edges("human_review", route_after_review)

app = graph.compile(checkpointer=MemorySaver())       # 2. required for interrupt()


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "greeting-001"}}     # 3.

    # -- the graph runs until interrupt(), then invoke RETURNS --------------
    result = app.invoke({"messages": [
        SystemMessage(content="You write greetings. One warm sentence, no preamble."),
        HumanMessage(content="Write a greeting for Shubham, who is celebrating a birthday."),
    ]}, config=config)

    payload = result["__interrupt__"][0].value
    print("1. PAUSED, and invoke returned. The UI would get:")
    print(f"     type  : {payload['type']}")
    print(f"     draft : {payload['draft'][:90]}")

    # -- resume with feedback: the node re-runs, then the graph loops -------
    result = app.invoke(Command(resume="revise: make it much more enthusiastic"), config=config)
    payload = result["__interrupt__"][0].value
    print("\n2. resumed with 'revise' -> drafted again, paused again:")
    print(f"     draft : {payload['draft'][:90]}")

    # -- resume with approval: this time the router sends us to END ---------
    result = app.invoke(Command(resume="approve"), config=config)
    print("\n3. resumed with 'approve':")
    print(f"     final : {result['messages'][-1].content[:90]}")

    print(f"\nhuman_review was entered {len(ENTRIES)} times for 2 pauses --")
    print("every resume re-ran it from the top (point 5), it did not continue")
    print("below interrupt(). Put a side effect above that call and it repeats.")

# Exercises:
# 1. Resume with "revise: ..." twice before approving. The entry count climbs
#    with it -- each pause costs one extra run of the lines above interrupt().
# 2. Move ENTRIES.append(...) below the interrupt() call. Now it logs once
#    per pause, because that half only runs after a resume arrives.
# 3. Remove checkpointer=MemorySaver(). Read the error: the pause has nowhere
#    to live (point 2).
# 4. Print app.get_state(config).next while paused -- it names the node the
#    graph will re-enter.
# 5. Resume with "reject" instead. route_after_review treats anything that is
#    not "approve" as a revision, so it loops forever. Add the third branch.
