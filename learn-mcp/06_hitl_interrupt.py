"""Lesson 06 -- Human-in-the-Loop: pause a tool, ask the user, resume
=====================================================================

greet() asks the user two things before it finishes -- "which language?",
then "is this greeting OK?" -- pausing each time and resuming with the answer.

  1. INTERRUPT  return status "interrupted" + an interrupt {type, message, payload, actions}
                + a continuation_token (a bookmark to the saved state)
  2. RESUME     the next call sends the answer in the request's _meta:
                {"continuation_token": ..., "user_response": {"action": ...}}
  3. ACTIONS    pick language -> draft -> REVIEW:  approve | refine (review again) | reject

  ┌──────────┐  interrupt  ┌──────────────┐  call_tool   ┌──────────────────────────┐
  │ FRONTEND │ ◄────────── │   BACKEND    │ ───────────► │ MCP SERVER  greet()      │
  │ shows UI │             │ (MCP client, │ ◄─────────── │ SESSIONS: token -> state │
  │ for type,│  answer     │  checkpoint) │  interrupted │                          │
  │ buttons  │ ──────────► │ resumes with │  / completed │                          │
  └──────────┘             │ meta={...}   │              └──────────────────────────┘
                           └──────────────┘
  (here, main() plays backend + frontend: it prints the buttons and "clicks" them)

  first call ─► LANGUAGE_SELECTION ─"fr"─► REVIEW ─approve/reject─► completed
                                            ▲  │
                                            └──┘ refine

Run:  uv run python 06_hitl_interrupt.py

Maps to production (shared/interrupts/models.py, story-drafting/src/interrupts/):
  SkillInterrupt(type, message, payload, actions)  ~  interrupt() below
  .block() puts the UI payload in _meta.forwarded_blocks so the agent sees
  only a summary (lesson 10); the orchestrator checkpoints to DynamoDB and
  resumes with LangGraph interrupt().
"""

import asyncio
import uuid
from pydantic import BaseModel
from fastmcp import FastMCP, Client, Context
from fastmcp.tools import ToolResult

mcp = FastMCP("hitl-greetings")
SESSIONS: dict[str, dict] = {}                # saved state (production: DynamoDB)
HELLO = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}


class Action(BaseModel):                      # a button: label shown, value sent back
    label: str
    value: str
    style: str = "default"                    # default | primary | danger


class LanguagePayload(BaseModel):             # typed payloads: extra="forbid" turns a
    model_config = {"extra": "forbid"}        # typo'd field into an error
    candidates: list[str]


class ReviewPayload(BaseModel):
    model_config = {"extra": "forbid"}
    draft: str
    revision: int


def interrupt(token, type, message, payload, actions) -> ToolResult:
    return ToolResult(
        content=f"[INTERRUPT] {type}: {message}",         # the AGENT sees a short summary
        structured_content={                              # the UI gets everything
            "status": "interrupted",
            "interrupt": {"type": type, "message": message, "payload": payload.model_dump(),
                          "actions": [a.model_dump() for a in actions]},
            "continuation_token": token,
        },
    )


def review(token, state) -> ToolResult:
    return interrupt(token, "GREETING.REVIEW", "Review the greeting",
                     ReviewPayload(draft=state["draft"], revision=state["revision"]),
                     [Action(label="Approve", value="approve", style="primary"),
                      Action(label="Refine", value="refine"),
                      Action(label="Reject", value="reject", style="danger")])


@mcp.tool
def greet(name: str, ctx: Context) -> ToolResult:
    """Greet someone -- asks the user for a language, then for approval."""
    meta = ctx.request_context.meta
    answer = meta.model_dump() if meta else {}

    # 1. INTERRUPT -- first call: save state, ask for a language
    if "user_response" not in answer:
        token = f"ct_{uuid.uuid4().hex[:8]}"
        SESSIONS[token] = {"name": name, "step": "language"}
        return interrupt(token, "GREETING.LANGUAGE_SELECTION", f"Which language for {name}?",
                         LanguagePayload(candidates=list(HELLO)),
                         [Action(label=code.upper(), value=code) for code in HELLO])

    # 2. RESUME -- load the saved state
    token = answer["continuation_token"]
    state, action = SESSIONS[token], answer["user_response"]["action"]

    # 3. ACTIONS
    if state["step"] == "language":
        state.update(step="review", language=action, revision=1,
                     draft=f"{HELLO[action]}, {state['name']}! Welcome to the team.")
        return review(token, state)
    if action == "refine":
        state["draft"] = f"{HELLO[state['language']]}, {state['name']}. A pleasure to welcome you."
        state["revision"] += 1
        return review(token, state)
    del SESSIONS[token]                                   # approve or reject: done
    return ToolResult(content=state["draft"] if action == "approve" else "Rejected.",
                      structured_content={"status": "completed", "action_taken": action,
                                          "greeting": state["draft"] if action == "approve" else None})


async def main():
    async with Client(mcp) as client:

        async def click(token, action):                   # the user clicks a button
            meta = {"continuation_token": token, "user_response": {"action": action}}
            return (await client.call_tool("greet", {"name": "Shubham"}, meta=meta)).structured_content

        r = await client.call_tool("greet", {"name": "Shubham"})
        sc, token = r.structured_content, r.structured_content["continuation_token"]
        print("1. agent sees:", r.content[0].text)        # [INTERRUPT] GREETING.LANGUAGE_SELECTION: ...
        print("   buttons   :", [a["label"] for a in sc["interrupt"]["actions"]])   # ['EN', 'FR', 'DE']

        i = (await click(token, "fr"))["interrupt"]
        print("2. click FR  :", i["type"], "rev", i["payload"]["revision"], "|", i["payload"]["draft"])

        i = (await click(token, "refine"))["interrupt"]
        print("3. refine    :", i["type"], "rev", i["payload"]["revision"], "|", i["payload"]["draft"])

        r = await click(token, "approve")
        print("4. approve   :", r["status"], "|", r["greeting"], "| state left:", SESSIONS)

    try:                                                  # extra="forbid" catches typos
        ReviewPayload(draft="Hi", revision=1, revison=2)
    except Exception as e:
        print("5. typo      :", type(e).__name__, "- 'revison' is not a field")


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Click "reject" instead of "approve". What comes back?
# 2. Add a third type, GREETING.STYLE_SELECTION (formal / casual), before the review.
# 3. Resume with an unknown token -- return a clear error instead of crashing.
