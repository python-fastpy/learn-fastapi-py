"""Lesson 06 -- Interruption: pause a tool, ask the user, resume
================================================================

greet() cannot finish on its own: it needs a language, then an approval. So
it returns twice with a QUESTION instead of an answer, and gets called again
with each reply. Four calls, one conversation.

  THE TWO CHANNELS -- this is the whole mechanism:

    OUT   the question rides in the RESULT     structured_content = {
          (the shape from lesson 05)             "status": "interrupted",
                                                 "interrupt": {type, message,
                                                               payload, actions},
                                                 "continuation_token": "ct_..."}

    BACK  the answer rides in the REQUEST      call_tool("greet", {"name": ...},
          as _meta -- a SIBLING of the            meta={"continuation_token": ...,
          arguments, not one of them                    "user_response": {...}})
          (lesson 14 shows it on the wire)     tool reads ctx.request_context.meta

  NOTHING IS SUSPENDED. Each resume is a brand-new call that enters greet()
  at the first line. No paused function is waiting to be woken: the token is
  just a key into SESSIONS, and the tool rebuilds its context from that every
  time. Read the `if` at the top of greet() as "is this a fresh start, or a
  reply?" -- that branch IS the resume.
  (LangGraph's interrupt() in lesson 13 does NOT differ here, despite how it
  reads: ainvoke() returns too, and on resume the node is RE-RUN from its
  first line, with interrupt() handing back the recorded answer. What the
  framework owns is the bookkeeping -- the checkpointer and the re-entry --
  not a frozen stack. Anything before its interrupt() therefore runs twice.)

  WHY A TOKEN, NOT A HELD CONNECTION: the state lives in a store, so the
  reply can arrive minutes later, from a different container, over a new HTTP
  connection (lesson 02's stateless_http=True). A held connection could not
  survive any of that.

  ┌──────────┐  interrupt  ┌──────────────┐  call_tool   ┌──────────────────────────┐
  │ FRONTEND │ ◄────────── │   BACKEND    │ ───────────► │ MCP SERVER  greet()      │
  │ shows UI │             │ (MCP client, │ ◄─────────── │ SESSIONS: token -> state │
  │ for type,│  answer     │  checkpoint) │  interrupted │                          │
  │ buttons  │ ──────────► │ resumes with │  / completed │                          │
  └──────────┘             │ meta={...}   │              └──────────────────────────┘
                           └──────────────┘
  (here main() plays both: it prints the buttons and clicks them)

  CALL 1  greet("Shubham")        -> interrupted  LANGUAGE_SELECTION
  CALL 2  + answer "fr"           -> interrupted  REVIEW, revision 1
  CALL 3  + answer "refine"       -> interrupted  REVIEW, revision 2   <- a loop
  CALL 4  + answer "approve"      -> completed,   and the token is dropped

Run:  uv run python 06_hitl_interrupt.py       (clicks its own buttons)
  or: uv run python 06_interactive.py         (YOU click them, same tool)

Maps to production (shared/interrupts/, story-drafting/src/interrupts/):
  SkillInterrupt(type, message, payload, actions) ~ ask() below. The
  orchestrator checkpoints to DynamoDB instead of a dict, and .block() keeps
  the payload out of the agent's context via _meta.forwarded_blocks (L09).

NOTE ON A SECOND WAY TO DO THIS: FastMCP itself now ships an official,
spec-level version of the same "ask, then resume" idea --
`InputRequiredResult` (see learn-fastmcp-server lesson 15). The mechanism
here predates that and is NOT the same wire shape (this uses a hand-rolled
continuation_token in _meta; FastMCP's uses input_requests/input_responses
on the result itself). Both solve "pause a tool, ask, resume" -- this one
is the production convention this codebase actually runs; lesson 15 is
what the MCP spec itself now standardizes. Know both; don't mix them in
one server.
"""

import asyncio
import uuid

from fastmcp import Client, Context, FastMCP
from fastmcp.tools import ToolResult

mcp = FastMCP("hitl-greetings")
SESSIONS: dict[str, dict] = {}                # token -> saved state (production: DynamoDB)
HELLO = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}


def ask(token: str, kind: str, question: str, buttons: list[str], **payload) -> ToolResult:
    """Stop and ask. The question goes out; the token says how to come back."""
    return ToolResult(
        content=f"[INTERRUPT] {kind}: {question}",     # the AGENT sees only this line
        structured_content={                          # the UI gets the whole thing
            "status": "interrupted",
            "interrupt": {"type": kind, "message": question,
                          "payload": payload, "actions": buttons},
            "continuation_token": token,              # the bookmark
        },
    )


def review(token: str, state: dict) -> ToolResult:
    """The REVIEW question -- asked once per revision, so it lives in a helper."""
    return ask(token, "GREETING.REVIEW", "Review the greeting",
               ["approve", "refine", "reject"],
               draft=state["draft"], revision=state["revision"])


@mcp.tool
def greet(name: str, ctx: Context) -> ToolResult:
    """Greet someone -- asks for a language, then for approval."""
    # EVERY call lands here, resumes included. Nothing was paused, so the
    # first job is always: fresh start, or a reply to an earlier question?
    meta = ctx.request_context.meta
    answer = meta.model_dump() if meta else {}

    # --- fresh start: no answer attached ------------------------------------
    if "user_response" not in answer:
        token = f"ct_{uuid.uuid4().hex[:8]}"
        SESSIONS[token] = {"name": name, "step": "language"}
        return ask(token, "GREETING.LANGUAGE_SELECTION", f"Which language for {name}?",
                   buttons=list(HELLO), candidates=list(HELLO))

    # --- a reply: the token says which conversation this belongs to ---------
    token = answer["continuation_token"]
    state = SESSIONS[token]                           # everything we knew last time
    action = answer["user_response"]["action"]

    if state["step"] == "language":                   # they picked a language
        state["step"] = "review"
        state["language"] = action
        state["revision"] = 1
        state["draft"] = f"{HELLO[action]}, {state['name']}! Welcome to the team."
        return review(token, state)                   # ask the NEXT question

    if action == "refine":                            # ask the SAME question again
        state["revision"] += 1
        state["draft"] = f"{HELLO[state['language']]}, {state['name']}. A pleasure to welcome you."
        return review(token, state)

    # approve or reject: the conversation is over, so drop the saved state
    del SESSIONS[token]
    approved = action == "approve"
    return ToolResult(
        content=state["draft"] if approved else "Rejected.",
        structured_content={"status": "completed", "action_taken": action,
                            "greeting": state["draft"] if approved else None},
    )


async def main():
    async with Client(mcp) as client:
        # CALL 1 -- no meta, so greet() takes the "fresh start" branch
        r = await client.call_tool("greet", {"name": "Shubham"})
        sc = r.structured_content
        token = sc["continuation_token"]
        print("CALL 1  greet('Shubham') ->", sc["status"])
        print("  agent sees :", r.content[0].text)
        print("  buttons    :", sc["interrupt"]["actions"])
        print("  token      :", token)
        print("  server kept:", SESSIONS[token])

        async def click(action: str) -> dict:
            """One button press = one NEW call, with the answer in _meta."""
            meta = {"continuation_token": token, "user_response": {"action": action}}
            r = await client.call_tool("greet", {"name": "Shubham"}, meta=meta)
            return r.structured_content

        for n, action in enumerate(("fr", "refine", "approve"), start=2):
            sc = await click(action)
            print(f"\nCALL {n}  + answer {action!r} ->", sc["status"])
            if sc["status"] == "interrupted":
                payload = sc["interrupt"]["payload"]
                print(f"  asks        : {sc['interrupt']['type']} (revision {payload['revision']})")
                print(f"  draft       : {payload['draft']}")
                print(f"  server kept : {SESSIONS[token]}")
            else:
                print(f"  greeting    : {sc['greeting']}")
                print(f"  server kept : {SESSIONS}   <- token dropped, conversation over")

        print("\nFour calls to the same tool. It never paused -- it re-entered")
        print("three times and reloaded its state from the token each time.")


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Click "reject" instead of "approve". What comes back, and what is left
#    in SESSIONS?
# 2. Resume with a token that doesn't exist. Right now SESSIONS[token] raises
#    KeyError, which reaches the caller as the unhelpful "Error calling tool
#    'greet': 'ct_...'". Return a clear "unknown or expired token" instead --
#    a real UI can always send a stale token, because state expires.
# 3. Delete the `del SESSIONS[token]` line. Nothing breaks visibly -- which
#    is the point: that is a state leak, and in production it costs money.
# 4. Add GREETING.STYLE_SELECTION (formal / casual) between language and
#    review. Notice you add a `step`, not a new tool.
# 5. Make the payloads typed: a pydantic model per interrupt type with
#    model_config = {"extra": "forbid"}, so `revison=2` is a startup error
#    rather than a field the UI silently never receives.
# 6. Give buttons a label and a style (["Approve" / primary, "Reject" /
#    danger]) instead of bare strings -- the UI needs both, the tool doesn't.
