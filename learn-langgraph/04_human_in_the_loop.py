"""
Lesson 10 (LangGraph 4): Human-in-the-Loop
=============================================
Goal: Implement interrupt/resume with LangGraph checkpointing.

What you'll learn:
  - interrupt() to pause graph execution
  - MemorySaver checkpointer (DynamoDB in production)
  - Resuming from a checkpoint with Command(resume=...)
  - Thread-based session isolation

Run:
  uv run python 04_human_in_the_loop.py

Production parallel:
  This is exactly how the Reuters backend handles skill interrupts:
  1. Skill returns status:"interrupted" -> orchestrator calls interrupt()
  2. State checkpointed to DynamoDB
  3. User responds in the UI
  4. Backend calls _resume_from_checkpoint() -> graph continues
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command


class DraftState(TypedDict):
    topic: str
    draft: str
    user_feedback: str
    status: str
    revision: int


def generate_draft(state: DraftState) -> dict:
    """Generate a news draft."""
    topic = state["topic"]
    revision = state.get("revision", 0) + 1
    draft = f"[Rev {revision}] Breaking: {topic}. Details emerging from multiple sources."
    print(f"  [generate] Created revision {revision}")
    return {"draft": draft, "revision": revision, "status": "draft_ready"}


def human_review(state: DraftState) -> dict:
    """Pause for human review using interrupt().

    This is the key function — interrupt() checkpoints the graph state
    and returns control to the caller. When resumed, the value passed
    to Command(resume=...) becomes the return value of interrupt().
    """
    draft = state["draft"]
    print(f"  [review] Presenting draft for review...")
    print(f"  [review] Draft: {draft}")

    # interrupt() pauses execution here.
    # The graph state is saved to the checkpointer.
    # When resumed, `user_response` receives the value from Command(resume=...).
    user_response = interrupt({
        "type": "STORY_REVIEW",
        "message": "Please review this draft",
        "draft": draft,
        "actions": ["approve", "refine", "reject"],
    })

    # This code runs AFTER resume
    print(f"  [review] User responded: {user_response}")
    return {"user_feedback": str(user_response), "status": "reviewed"}


def route_after_review(state: DraftState) -> str:
    """Route based on user feedback."""
    feedback = state.get("user_feedback", "")
    if "approve" in feedback.lower():
        return "publish"
    elif "reject" in feedback.lower():
        return "end"
    else:
        return "revise"


def revise_draft(state: DraftState) -> dict:
    """Revise based on feedback, then loop back for another review."""
    feedback = state["user_feedback"]
    draft = state["draft"]
    revised = f"{draft}\n[REVISED based on: {feedback}]"
    revision = state.get("revision", 1) + 1
    print(f"  [revise] Applying feedback, creating revision {revision}")
    return {"draft": revised, "revision": revision, "status": "revised"}


def publish(state: DraftState) -> dict:
    """Publish the approved draft."""
    print(f"  [publish] Publishing revision {state['revision']}!")
    return {"status": "published"}


# --- Build the graph ---

graph = StateGraph(DraftState)

graph.add_node("generate", generate_draft)
graph.add_node("review", human_review)
graph.add_node("revise", revise_draft)
graph.add_node("publish", publish)

graph.add_edge(START, "generate")
graph.add_edge("generate", "review")
graph.add_conditional_edges(
    "review",
    route_after_review,
    {"publish": "publish", "revise": "revise", "end": END},
)
graph.add_edge("revise", "review")  # loop: revise -> review again
graph.add_edge("publish", END)

# MemorySaver is an in-memory checkpointer (for learning).
# Production uses DynamoDB: dynamodb_checkpointer.py
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    # Thread config — like a session ID. Each thread has its own checkpoint.
    # In production, this is the session_id from DynamoDB.
    config = {"configurable": {"thread_id": "demo-session-001"}}

    print("=" * 60)
    print("Step 1: Start the graph — it will generate a draft and pause")
    print("=" * 60)

    initial_state: DraftState = {
        "topic": "Tesla announces record deliveries",
        "draft": "",
        "user_feedback": "",
        "status": "",
        "revision": 0,
    }

    # invoke() runs until interrupt() is called, then returns
    result = app.invoke(initial_state, config=config)
    print(f"\n  State after interrupt: status={result['status']}")

    # Check what the interrupt payload looks like
    state = app.get_state(config)
    print(f"  Graph paused at node: {state.next}")
    # state.tasks contains the interrupt payload
    for task in state.tasks:
        if hasattr(task, 'interrupts') and task.interrupts:
            for intr in task.interrupts:
                print(f"  Interrupt payload: {intr.value}")

    # --- Simulate user requesting refinement ---
    print(f"\n{'='*60}")
    print("Step 2: User requests refinement")
    print("=" * 60)

    result = app.invoke(
        Command(resume="refine: add delivery numbers and analyst quotes"),
        config=config,
    )
    print(f"\n  State after 2nd interrupt: status={result['status']}")

    # --- Simulate user approving ---
    print(f"\n{'='*60}")
    print("Step 3: User approves")
    print("=" * 60)

    result = app.invoke(
        Command(resume="approve"),
        config=config,
    )
    print(f"\n  Final state: status={result['status']}")
    print(f"  Final draft:\n{result['draft']}")

    # Show graph
    print(f"\n{'='*60}")
    print("Graph Structure:")
    print(app.get_graph().draw_mermaid())


# ============================================================
# EXERCISES:
#
# 1. Add a second interrupt after "publish" that asks for
#    confirmation before actually publishing
# 2. Implement "reject" -> return a rejection message and end
# 3. Create a new thread_id and verify it has independent state
# 4. Try resuming with Command(resume={"action": "refine",
#    "edits": "..."}) — structured resume data
# ============================================================
