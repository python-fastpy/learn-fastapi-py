"""Lesson 05 -- Multi-Agent: Specialized Agents on One Server
==============================================================

WHY THIS MATTERS:
  In production, different tasks need different agents. Reuters has
  specialized agents for drafting stories, searching archives, and
  building urgents. CopilotKit lets you register multiple agents on
  the same FastAPI server, each with its own tools and personality.

WHAT YOU'LL LEARN:
  1. Register multiple LangGraphAGUIAgent instances on different paths
  2. Each agent has its own system prompt, tools, and model config
  3. The frontend can target a specific agent via the URL path
  4. Pattern: one server, many specialists

Concepts:
  - Multi-agent routing: each agent has its own endpoint path
  - Agent specialization: different tools and prompts per agent
  - In production, Reuters routes to agents based on the user's intent
  - The frontend connects via <CopilotKit url="http://localhost:8000/{path}">

Flow:
  Frontend picks agent path based on task:

  /copilotkit/writer   → Writing Agent   (draft, rewrite, headlines)
  /copilotkit/research → Research Agent  (search, fact-check, analyze)
  /copilotkit/editor   → Editor Agent    (style, grammar, AP/Reuters rules)

Run:  uv run python 05_multi_agent.py

EXPECTED OUTPUT:
  INFO:     Uvicorn running on http://0.0.0.0:8000

  Three agents available:
    POST /copilotkit/writer   — story writing
    POST /copilotkit/research — research and search
    POST /copilotkit/editor   — copy editing

  Default (for frontend examples that use /copilotkit):
    POST /copilotkit           — redirects to the writer agent

USED IN REUTERS:
  reuters-assistant_backend/src/services/langgraph_mcp_orchestrator.py
    — Routes to different MCP skill servers based on workflow selection
  reuters-assistant_backend/src/services/mcp_server_registry.py
    — Registry of all available MCP servers and their capabilities
  reuters-assistant_backend/src/services/fast_path_matcher.py
    — Fast-path routing: bypasses LLM for well-known patterns
"""

import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: Set OPENAI_API_KEY in your .env file")
    exit(1)

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from copilotkit import CopilotKitMiddleware, LangGraphAGUIAgent
from ag_ui_langgraph import add_langgraph_fastapi_endpoint


# =================================================================
# STEP 1: DEFINE AGENT-SPECIFIC TOOLS
# =================================================================

# -- Writer tools --
@tool
def draft_headline(topic: str, style: str = "reuters") -> str:
    """Generate 3 headline options for a topic.

    Args:
        topic: What the headline is about
        style: Writing style (reuters, ap, tabloid)
    """
    styles = {
        "reuters": [
            f"{topic} — key developments emerge",
            f"UPDATE 1-{topic} shows significant movement",
            f"BRIEF-{topic} in focus as markets react",
        ],
        "ap": [
            f"{topic}: What you need to know",
            f"Developments in {topic} draw attention",
            f"{topic} update: Latest details",
        ],
        "tabloid": [
            f"BREAKING: {topic} SHOCKER!",
            f"You won't BELIEVE what happened with {topic}",
            f"{topic}: The story that has EVERYONE talking",
        ],
    }
    options = styles.get(style, styles["reuters"])
    return "Headline options:\n" + "\n".join(f"  {i+1}. {h}" for i, h in enumerate(options))


@tool
def expand_paragraph(text: str, direction: str = "detail") -> str:
    """Suggest how to expand a paragraph.

    Args:
        text: The paragraph to expand
        direction: How to expand: 'detail', 'context', 'quotes'
    """
    word_count = len(text.split())
    return (
        f"Current paragraph: {word_count} words. "
        f"Suggestion ({direction}): Add 2-3 sentences with "
        f"{'specific data points' if direction == 'detail' else 'background context' if direction == 'context' else 'expert quotes'}."
    )


# -- Research tools --
@tool
def quick_search(query: str) -> str:
    """Quick search for background information.

    Args:
        query: What to search for
    """
    return f"Found 8 relevant sources for '{query}'. Top 3: industry report (2026), analyst note (Q2), Reuters archive (Aug 2026)."


@tool
def verify_fact(statement: str) -> str:
    """Verify a factual claim.

    Args:
        statement: The claim to verify
    """
    return f"Verification result for '{statement}': Plausible based on available data. Recommend cross-referencing with primary sources."


# -- Editor tools --
@tool
def check_style(text: str) -> str:
    """Check text against Reuters style guidelines.

    Args:
        text: Text to check
    """
    issues = []
    if "%" in text and "percent" not in text:
        issues.append("Reuters style: spell out 'percent' (not %)")
    if text.count("!") > 0:
        issues.append("Avoid exclamation marks in news copy")
    if len(text.split()) > 0 and text.split()[0].isupper() and len(text.split()[0]) > 4:
        issues.append("Don't shout — avoid ALL CAPS words over 4 letters")
    if not issues:
        return "Text passes style check."
    return "Style issues:\n" + "\n".join(f"  - {i}" for i in issues)


@tool
def suggest_trim(text: str, target_words: int = 50) -> str:
    """Suggest how to trim text to a target word count.

    Args:
        text: Text to trim
        target_words: Target word count
    """
    current = len(text.split())
    if current <= target_words:
        return f"Already at {current} words (target: {target_words}). No trimming needed."
    excess = current - target_words
    return f"Current: {current} words. Need to cut {excess} words. Suggestions: remove adverbs, combine sentences, cut redundant phrases."


# =================================================================
# STEP 2: CREATE SPECIALIZED AGENTS
# =================================================================

writer_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0.5),
    tools=[draft_headline, expand_paragraph],
    prompt="You are a Reuters news writer. Help draft and improve story content. Be creative but accurate.",
    middleware=[CopilotKitMiddleware()],
)

research_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0.2),
    tools=[quick_search, verify_fact],
    prompt="You are a research assistant. Help find information and verify facts. Be thorough and cite sources.",
    middleware=[CopilotKitMiddleware()],
)

editor_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0.1),
    tools=[check_style, suggest_trim],
    prompt="You are a copy editor following Reuters style. Check grammar, style, and brevity. Be precise.",
    middleware=[CopilotKitMiddleware()],
)


# =================================================================
# STEP 3: MOUNT ALL AGENTS ON FASTAPI
# =================================================================

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Learn CopilotKit - Lesson 05")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agents = [
    ("writer", "Story writing and drafting", writer_agent, "/copilotkit/writer"),
    ("research", "Research and fact-checking", research_agent, "/copilotkit/research"),
    ("editor", "Copy editing and style checking", editor_agent, "/copilotkit/editor"),
]

for name, desc, graph, path in agents:
    add_langgraph_fastapi_endpoint(
        app=app,
        agent=LangGraphAGUIAgent(name=name, description=desc, graph=graph),
        path=path,
    )

# Default agent — so frontend examples that use /copilotkit still work
add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(name="writer", description="Default writing assistant", graph=writer_agent),
    path="/copilotkit",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "lesson": "05_multi_agent",
        "agents": {name: path for name, _, _, path in agents},
    }


if __name__ == "__main__":
    print("\n  Lesson 05: Multi-Agent Server")
    print("  ==============================")
    for name, desc, _, path in agents:
        print(f"    {path:30s} → {name} ({desc})")
    print(f"    {'POST /copilotkit':30s} → default (writer)")
    print("\n  Change the frontend URL to target a specific agent:")
    print('    <CopilotKit url="http://localhost:8000/copilotkit/research">')
    print()

    uvicorn.run(
        "05_multi_agent:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

    # -- Exercise ---------------------------------------------------------
    # 1. Add a fourth agent: "translator" that translates text between languages
    # 2. Try the same prompt with different agents — notice the different responses
    # 3. Modify 1-basic-chat.tsx to point to /copilotkit/editor instead
    # 4. Can you make the frontend switch agents dynamically? (hint: state + URL)
