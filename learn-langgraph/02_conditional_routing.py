"""
Lesson 8 (LangGraph 2): Conditional Routing
=============================================
Goal: Route execution through different paths based on state.

What you'll learn:
  - add_conditional_edges() for dynamic routing
  - Router functions that inspect state and return next node names
  - Multi-path graphs (not just linear)

Run:
  uv run python 02_conditional_routing.py

Production parallel:
  The backend orchestrator routes to different execution strategies
  (none, single, sequential, parallel) based on the LLM's analysis
  of what tools are needed.
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END


class StoryState(TypedDict):
    story_type: str       # "spot", "bulletin", "buzz", or "urgent"
    topic: str
    urgency: str          # "breaking", "developing", "routine"
    draft: str
    status: str


# --- Nodes for different story types ---

def classify_node(state: StoryState) -> dict:
    """Classify the story type and urgency."""
    topic = state["topic"].lower()
    if "breaking" in topic or "urgent" in topic:
        return {"urgency": "breaking", "story_type": "urgent"}
    elif "earnings" in topic or "quarterly" in topic:
        return {"urgency": "routine", "story_type": "buzz"}
    elif "bulletin" in topic:
        return {"urgency": "developing", "story_type": "bulletin"}
    else:
        return {"urgency": "routine", "story_type": "spot"}


def spot_story_node(state: StoryState) -> dict:
    print(f"  [spot] Drafting spot story about: {state['topic']}")
    return {"draft": f"SPOT: {state['topic']} — Details emerging.", "status": "drafted"}


def bulletin_node(state: StoryState) -> dict:
    print(f"  [bulletin] Drafting bulletin about: {state['topic']}")
    return {"draft": f"BULLETIN: {state['topic']} — Developing story.", "status": "drafted"}


def buzz_node(state: StoryState) -> dict:
    print(f"  [buzz] Drafting buzz about: {state['topic']}")
    return {"draft": f"BUZZ: {state['topic']} — Market reaction noted.", "status": "drafted"}


def urgent_node(state: StoryState) -> dict:
    print(f"  [urgent] URGENT draft about: {state['topic']}")
    return {"draft": f"URGENT: {state['topic']} — DEVELOPING", "status": "urgent_drafted"}


def review_node(state: StoryState) -> dict:
    print(f"  [review] Reviewing {state['story_type']} story")
    return {"status": "reviewed"}


def fast_publish_node(state: StoryState) -> dict:
    print(f"  [fast_publish] Fast-tracking urgent story!")
    return {"status": "published"}


# --- Router function ---
# Returns the name of the next node based on state.

def route_by_type(state: StoryState) -> Literal["spot", "bulletin", "buzz", "urgent"]:
    """Route to the appropriate drafting node based on story type."""
    return state["story_type"]


def route_after_draft(state: StoryState) -> Literal["review", "fast_publish"]:
    """Urgents skip review and go straight to fast publish."""
    if state["urgency"] == "breaking":
        return "fast_publish"
    return "review"


# --- Build the graph ---

graph = StateGraph(StoryState)

# Add all nodes
graph.add_node("classify", classify_node)
graph.add_node("spot", spot_story_node)
graph.add_node("bulletin", bulletin_node)
graph.add_node("buzz", buzz_node)
graph.add_node("urgent", urgent_node)
graph.add_node("review", review_node)
graph.add_node("fast_publish", fast_publish_node)

# Linear start
graph.add_edge(START, "classify")

# Conditional routing after classification
graph.add_conditional_edges(
    "classify",
    route_by_type,
    {
        "spot": "spot",
        "bulletin": "bulletin",
        "buzz": "buzz",
        "urgent": "urgent",
    },
)

# All drafting nodes -> conditional: review or fast publish
for node in ["spot", "bulletin", "buzz", "urgent"]:
    graph.add_conditional_edges(node, route_after_draft)

# Both endpoints -> END
graph.add_edge("review", END)
graph.add_edge("fast_publish", END)

app = graph.compile()

if __name__ == "__main__":
    test_cases = [
        {"topic": "Apple quarterly earnings beat estimates", "story_type": "", "urgency": "", "draft": "", "status": ""},
        {"topic": "BREAKING: Major earthquake hits Tokyo", "story_type": "", "urgency": "", "draft": "", "status": ""},
        {"topic": "Fed bulletin on interest rates", "story_type": "", "urgency": "", "draft": "", "status": ""},
        {"topic": "Tesla announces new factory in Berlin", "story_type": "", "urgency": "", "draft": "", "status": ""},
    ]

    for case in test_cases:
        print(f"\n{'='*50}")
        print(f"Topic: {case['topic']}")
        print(f"{'='*50}")
        result = app.invoke(case)
        print(f"  Type: {result['story_type']}")
        print(f"  Urgency: {result['urgency']}")
        print(f"  Status: {result['status']}")
        print(f"  Draft: {result['draft'][:60]}...")

    # Show the graph structure
    print(f"\n=== Graph Structure ===")
    print(app.get_graph().draw_mermaid())


# ============================================================
# EXERCISES:
#
# 1. Add a "priority" field and route high-priority non-urgent
#    stories to a "priority_review" node (faster turnaround)
# 2. Add a "language" field and route to different nodes for
#    English vs other languages
# 3. Create a sub-graph for the buzz path that has its own
#    internal RIC validation step
# ============================================================
