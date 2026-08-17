"""Lesson 09 — Human-in-the-Loop
=================================
Concepts:
  - interrupt(): pause the graph and wait for human input
  - Command(resume=...): send the human's response back
  - interrupt_before / interrupt_after: pause at specific nodes
  - This is EXACTLY how your skills' interrupt system works!

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

  human_review calls interrupt() -- graph PAUSES, waits for
  Command(resume=...). If user says "revise", loops back to
  draft_greeting. If "approve", exits to END.

** Requires .env with orchestrator credentials **

Run:  uv run python 09_human_in_the_loop.py
"""

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from llm_helper import get_llm


llm = get_llm(model="gpt-4o")


def draft_greeting(state: MessagesState) -> dict:
    """LLM drafts a greeting."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def human_review(state: MessagesState) -> dict:
    """Pause for human approval. This is where interrupt() fires."""
    last_ai_message = state["messages"][-1].content

    # interrupt() pauses the graph and sends this value to the caller
    decision = interrupt({
        "type": "greeting_review",
        "draft": last_ai_message,
        "prompt": "Approve this greeting? (approve / revise: <feedback>)",
    })

    # When resumed, `decision` contains what the human sent back
    if decision.startswith("approve"):
        return {"messages": [AIMessage(content=f"APPROVED: {last_ai_message}")]}
    else:
        feedback = decision.replace("revise:", "").strip()
        return {
            "messages": [
                HumanMessage(content=f"Please revise the greeting. Feedback: {feedback}")
            ]
        }


def route_after_review(state: MessagesState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.content.startswith("APPROVED"):
        return END
    return "draft_greeting"


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

    config = {"configurable": {"thread_id": "greeting-001"}}

    # -- Step 1: Start the graph -- it will pause at human_review ------
    print("=== Starting draft ===")
    result = app.invoke(
        {"messages": [
            SystemMessage(content="You are a greeting writer. Write one warm, personalized greeting."),
            HumanMessage(content="Write a greeting for Alice who is celebrating her birthday."),
        ]},
        config=config,
    )

    # The graph is now PAUSED at interrupt()
    # In production, the frontend would show the draft to the user
    state = app.get_state(config)
    interrupt_data = state.tasks[0].interrupts[0].value
    print(f"\nDraft: {interrupt_data['draft'][:200]}")
    print(f"Prompt: {interrupt_data['prompt']}")

    # -- Step 2: Simulate human sending "revise" ----------------------
    print("\n=== Human says: revise ===")
    result2 = app.invoke(
        Command(resume="revise: Make it more enthusiastic"),
        config=config,
    )

    # The graph drafted a new greeting and paused again
    state2 = app.get_state(config)
    if state2.tasks:
        interrupt_data2 = state2.tasks[0].interrupts[0].value
        print(f"\nRevised draft: {interrupt_data2['draft'][:200]}")

        # -- Step 3: Approve this time --------------------------------
        print("\n=== Human says: approve ===")
        result3 = app.invoke(
            Command(resume="approve"),
            config=config,
        )
        print(f"\nFinal: {result3['messages'][-1].content[:200]}")

    # -- Key takeaway -------------------------------------------------
    # interrupt() -> graph pauses -> checkpoint saved -> human responds
    # -> Command(resume=...) -> graph continues from exactly where it
    # paused.
    #
    # This pattern works for any review loop: greetings, farewells,
    # drafts, approvals. The graph remembers its full state across
    # pauses via the checkpointer (MemorySaver here, DynamoDB in prod).
    #
    # -- Exercise -----------------------------------------------------
    # 1. Add a max_revisions counter to state
    # 2. After 3 revisions, auto-approve with a warning
    # 3. Test the loop limit
