"""Lesson 07 -- Context window management: a long-running agent fills up
=============================================================================

Lesson 01's `messages` list only ever held 3 entries. A real agent working
a long task can accumulate dozens of tool results -- eventually that list
is too big to send to the model at all (there's a hard token limit) or too
expensive to send every single call (you pay per token, every turn, for
history that's barely relevant anymore).

    messages grows: [sys, tool1, tool2, ..., tool50]
         │
         ▼
    TRUNCATION                         SUMMARIZATION
    keep: system + last N              keep: system + ONE summary of
    verbatim messages                  everything older + last N verbatim
    drop everything older              messages
    (cheap, but older facts            (costs one extra summarization
     are GONE, not just hidden)         pass, but older facts survive
                                        in compressed form)

This lesson uses `len(str(...))` as a stand-in for a real token counter
(e.g. `tiktoken`) -- the exact number is irrelevant, only the SHAPE of
"it grows, then a strategy brings it back down" matters here.

Run:  uv run python 07_context_window_management.py
"""

BUDGET = 400   # a tiny fake budget, on purpose, so the overflow shows up fast


def fake_token_count(messages: list[dict]) -> int:
    """A real agent would use a real tokenizer. The shape of the lesson
    doesn't change if you swap this one line for a real one."""
    return len(str(messages))


def build_long_history() -> list[dict]:
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for i in range(1, 11):
        messages.append({"role": "tool", "tool": "lookup_order", "result": f"order #{i}: shipped on day {i}"})
    return messages


def truncate(messages: list[dict], keep_last: int = 3) -> list[dict]:
    """Drop everything except the system message and the most recent N."""
    system = [m for m in messages if m["role"] == "system"]
    recent = [m for m in messages if m["role"] != "system"][-keep_last:]
    return system + recent


def summarize(messages: list[dict], keep_last: int = 3) -> list[dict]:
    """Compress everything OLDER than the last N into one message instead
    of dropping it -- a real version would ask a model to write this
    summary; here it's just a deterministic one-liner."""
    system = [m for m in messages if m["role"] == "system"]
    non_system = [m for m in messages if m["role"] != "system"]
    older, recent = non_system[:-keep_last], non_system[-keep_last:]

    if not older:
        return system + recent

    summary_text = f"(summarized {len(older)} earlier tool results: orders #1-#{len(older)}, all shipped)"
    return system + [{"role": "system", "content": summary_text}] + recent


if __name__ == "__main__":
    history = build_long_history()
    print(f"full history: {len(history)} messages, fake_token_count = {fake_token_count(history)}")
    print("over budget?", fake_token_count(history) > BUDGET)

    truncated = truncate(history)
    print(f"\ntruncated:   {len(truncated)} messages, fake_token_count = {fake_token_count(truncated)}")
    print("kept:", [m.get("result", m.get("content")) for m in truncated])

    summarized = summarize(history)
    print(f"\nsummarized:  {len(summarized)} messages, fake_token_count = {fake_token_count(summarized)}")
    print("kept:", [m.get("result", m.get("content")) for m in summarized])

    print(
        "\ntruncation is smaller, but orders #1-#7 are GONE, not just hidden;"
        "\nsummarization is slightly bigger, but a one-line trace of them survives."
    )

# Expected output:
#
# full history: 11 messages, fake_token_count = 885
# over budget? True
#
# truncated:   4 messages, fake_token_count = 311
# kept: ['You are a helpful assistant.', 'order #8: shipped on day 8', 'order #9: shipped on day 9', 'order #10: shipped on day 10']
#
# summarized:  5 messages, fake_token_count = 408
# kept: ['You are a helpful assistant.', '(summarized 7 earlier tool results: orders #1-#7, all shipped)', 'order #8: shipped on day 8', 'order #9: shipped on day 9', 'order #10: shipped on day 10']
#
# truncation is smaller, but orders #1-#7 are GONE, not just hidden;
# summarization is slightly bigger, but a one-line trace of them survives.
