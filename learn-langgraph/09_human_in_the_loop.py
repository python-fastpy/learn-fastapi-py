"""Lesson 09 — Human-in-the-Loop
=================================

WHY THIS MATTERS:
  Sometimes the AI shouldn't act alone -- a human needs to review, approve,
  or revise before the workflow continues. This is critical in newsrooms:
  an AI-drafted urgent needs editor review before publishing. The production
  assistant uses this exact pattern for every skill interrupt: draft -> pause
  -> human reviews -> approve or revise -> continue.

  interrupt() is the mechanism: it saves the graph's state to the
  checkpointer, pauses execution, and sends data to the caller. When the
  human responds, Command(resume=...) loads the saved state and continues
  from exactly where it stopped.

WHAT YOU'LL LEARN:
  1. interrupt(): pause the graph mid-execution and wait for human input
  2. Command(resume=...): send the human's response back to resume
  3. The review loop: draft -> pause -> human decides -> approve or revise
  4. Why checkpointers are REQUIRED for interrupts (state must persist)
  5. How this maps to every skill interrupt in the production assistant

How interrupts work under the hood:
  1. Graph runs until a node calls interrupt({...payload...})
  2. LangGraph saves the FULL state to the checkpointer (MemorySaver / DynamoDB)
  3. The interrupt payload is returned to the caller (frontend shows it)
  4. User makes a decision (approve, revise, reject)
  5. Caller sends Command(resume="approve") with the same thread_id
  6. LangGraph loads the checkpoint, passes the resume value to the node
  7. The node continues from the line AFTER interrupt() with the response

Concepts:
  - interrupt(payload): pauses graph, saves state, returns payload to caller
  - Command(resume=value): resumes graph, passes value to the interrupted node
  - Checkpointer is REQUIRED: interrupt saves state, resume loads it.
    Without a checkpointer, the graph has no memory across pauses.
  - The pattern: draft -> interrupt -> human decides -> approve (END) or
    revise (loop back to draft)
  - In production: interrupt payload includes EventType, draft content,
    and available actions

Graph:
  +-------+     +-----------------+     +--------------+
  | START | --> | draft_greeting  | --> | human_review |
  +-------+     +-----------------+     +--------------+
                       ^                     |
                       |          route_after_review()
                       |              /           \\
                       |             v             v
                       |        (revise)        +-----+
                       +--- loop back           | END |
                                                +-----+

  Execution trace:
    Step 1: invoke() -> draft_greeting runs -> human_review calls interrupt()
      -> Graph PAUSES, checkpoint saved
      -> Caller receives: {"type": "greeting_review", "draft": "...", ...}

    Step 2: invoke(Command(resume="revise: Make it more enthusiastic"))
      -> Graph RESUMES from interrupt(), decision = "revise: ..."
      -> human_review returns HumanMessage with feedback
      -> route_after_review -> "draft_greeting" (loop back)
      -> draft_greeting runs again -> human_review calls interrupt() again
      -> Graph PAUSES again

    Step 3: invoke(Command(resume="approve"))
      -> Graph RESUMES, decision = "approve"
      -> human_review returns AIMessage("APPROVED: ...")
      -> route_after_review -> END

Maps to:
  langgraph_mcp_orchestrator.py -> interrupt() + _resume_from_checkpoint()
  reuter-ai-assistant-skills-interrupt.component.tsx -> renders interrupt UI
  dynamodb_checkpointer.py -> persists state across interrupt pauses
  EventTypes: SPOT_STORY_REVIEW, NEWS_BUZZ.REVIEW, URGENT_BUILDER_REVIEW, etc.

PREREQUISITES: Lesson 08 (checkpointers -- interrupts REQUIRE checkpointing
  to save/load state)

EXPECTED OUTPUT:
  === Graph Diagram (Mermaid) ===
  (mermaid graph text)

  === Starting draft ===
  Draft: Happy birthday, Alice! Wishing you a wonderful day...
  Prompt: Approve this greeting? (approve / revise: <feedback>)

  === Human says: revise ===
  Revised draft: HAPPY BIRTHDAY, ALICE! What an incredible day...

  === Human says: approve ===
  Final: APPROVED: HAPPY BIRTHDAY, ALICE! What an incredible day...

** Requires .env with orchestrator credentials **

Run:  uv run python 09_human_in_the_loop.py
"""

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from llm_helper import get_llm


llm = get_llm(model="gpt-4o")


# ── Step 1: The draft node ──────────────────────────────────────────
# This node calls the LLM to generate a greeting draft. It runs on
# every cycle -- both the initial draft and any revision requested
# by the human. The LLM sees the full message history, so revision
# feedback from the human naturally guides the next draft.

def draft_greeting(state: MessagesState) -> dict:
    """LLM drafts a greeting."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


# ── Step 2: The interrupt node ──────────────────────────────────────
# This is where the magic happens. interrupt() does three things:
#   1. Saves the FULL graph state to the checkpointer
#   2. Pauses execution and returns the payload to the caller
#   3. When resumed, returns the human's response as `decision`
#
# Everything AFTER the interrupt() call only runs when the graph is
# resumed via Command(resume=...). The `decision` variable holds
# whatever the human sent back.

def human_review(state: MessagesState) -> dict:
    """Pause for human approval. This is where interrupt() fires."""
    last_ai_message = state["messages"][-1].content

    # interrupt() pauses the graph and sends this payload to the caller.
    # In production, this payload includes an EventType (e.g.,
    # SPOT_STORY_REVIEW) so the frontend knows which UI to render.
    decision = interrupt({
        "type": "greeting_review",
        "draft": last_ai_message,
        "prompt": "Approve this greeting? (approve / revise: <feedback>)",
    })

    # --- This code only runs AFTER the human responds ---
    # `decision` is the value from Command(resume=...).
    # If approved, wrap the draft in an APPROVED marker (signals END).
    # If revised, inject the feedback as a HumanMessage so the LLM
    # sees it on the next draft cycle.
    if decision.startswith("approve"):
        return {"messages": [AIMessage(content=f"APPROVED: {last_ai_message}")]}
    else:
        feedback = decision.replace("revise:", "").strip()
        return {
            "messages": [
                HumanMessage(content=f"Please revise the greeting. Feedback: {feedback}")
            ]
        }


# ── Step 3: The routing function ────────────────────────────────────
# After human_review, we check whether the human approved or revised.
# If approved (AIMessage starting with "APPROVED"), go to END.
# If revised (HumanMessage with feedback), loop back to draft_greeting
# so the LLM can try again with the feedback in context.

def route_after_review(state: MessagesState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.content.startswith("APPROVED"):
        return END
    return "draft_greeting"


# ── Step 4: Build the graph with a checkpointer ────────────────────
# The checkpointer (MemorySaver) is REQUIRED for interrupts. Without
# it, the graph has no way to save state when it pauses or load state
# when it resumes. In production, DynamoDB replaces MemorySaver so
# state persists across server restarts and container recycling.

graph = StateGraph(MessagesState)
graph.add_node("draft_greeting", draft_greeting)
graph.add_node("human_review", human_review)

graph.add_edge(START, "draft_greeting")
graph.add_edge("draft_greeting", "human_review")
graph.add_conditional_edges("human_review", route_after_review)

memory = MemorySaver()
app = graph.compile(checkpointer=memory)


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    # thread_id ties all invoke() calls to the SAME conversation.
    # The checkpointer uses this to save and load state across pauses.
    config = {"configurable": {"thread_id": "greeting-001"}}

    # -- Phase 1: Initial draft -- graph runs until interrupt() --------
    # The graph executes: START -> draft_greeting -> human_review.
    # Inside human_review, interrupt() fires: state is saved to the
    # checkpointer and the interrupt payload is returned to us.
    print("=== Starting draft ===")
    result = app.invoke(
        {"messages": [
            SystemMessage(content="You are a greeting writer. Write one warm, personalized greeting."),
            HumanMessage(content="Write a greeting for Alice who is celebrating her birthday."),
        ]},
        config=config,
    )

    # The graph is now PAUSED at interrupt(). In production, the backend
    # would return the interrupt payload via SSE, and the frontend
    # (reuter-ai-assistant-skills-interrupt.component.tsx) would render
    # the appropriate review UI based on the EventType.
    state = app.get_state(config)
    interrupt_data = state.tasks[0].interrupts[0].value
    print(f"\nDraft: {interrupt_data['draft'][:200]}")
    print(f"Prompt: {interrupt_data['prompt']}")

    # -- Phase 2: Human says "revise" -- graph resumes + loops --------
    # Command(resume=...) loads the checkpoint and passes the value to
    # the interrupted node. human_review sees decision="revise: ..."
    # and returns a HumanMessage with feedback. The router sends it
    # back to draft_greeting, which generates a new draft, then
    # human_review calls interrupt() AGAIN -- pausing a second time.
    print("\n=== Human says: revise ===")
    result2 = app.invoke(
        Command(resume="revise: Make it more enthusiastic"),
        config=config,
    )

    # The graph drafted a new greeting and paused again at interrupt()
    state2 = app.get_state(config)
    if state2.tasks:
        interrupt_data2 = state2.tasks[0].interrupts[0].value
        print(f"\nRevised draft: {interrupt_data2['draft'][:200]}")

        # -- Phase 3: Human approves -- graph completes ---------------
        # This time, human_review sees decision="approve", returns an
        # AIMessage starting with "APPROVED", and the router sends it
        # to END. The graph is complete.
        print("\n=== Human says: approve ===")
        result3 = app.invoke(
            Command(resume="approve"),
            config=config,
        )
        print(f"\nFinal: {result3['messages'][-1].content[:200]}")

    # -- Key takeaway -------------------------------------------------
    # interrupt() -> graph pauses -> checkpoint saved -> human responds
    # -> Command(resume=...) -> graph continues from exactly where it
    # paused. The human can revise as many times as needed -- the graph
    # loops back each time, accumulating feedback in the message history.
    #
    # This is the SAME pattern used in every production skill interrupt:
    #   - SPOT_STORY_REVIEW: draft -> editor reviews -> approve/revise
    #   - NEWS_BUZZ.REVIEW: buzz draft -> journalist reviews -> approve
    #   - URGENT_BUILDER_REVIEW: urgent -> editor reviews -> publish
    #
    # The checkpointer makes it durable: MemorySaver here (in-memory,
    # lost on restart), DynamoDB in production (persists across server
    # restarts, container recycling, and even deployments).
    #
    # Without a checkpointer, interrupt() would fail -- there's nowhere
    # to save the state when pausing or load it when resuming.
    #
    # -- Exercise -----------------------------------------------------
    # 1. Add a max_revisions counter to state
    # 2. After 3 revisions, auto-approve with a warning
    # 3. Test the loop limit
