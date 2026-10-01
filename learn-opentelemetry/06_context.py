"""Lesson 06 -- Context: the mechanism underneath every earlier lesson
=========================================================================

Every lesson so far used `start_as_current_span()` and, in lesson 05,
`inject()`/`extract()`. All four are built on ONE lower-level primitive:
`opentelemetry.context`. This lesson opens that box.

A Context is just an immutable key-value mapping. "The current context" is
whichever one is currently active for this thread/task. Four functions are
the entire API:

    context.set_value(key, value)   returns a NEW Context with that key set
                                     (does NOT touch the current one -- Context
                                      objects are immutable)
    context.attach(new_ctx)         makes new_ctx the current one, returns a
                                     Token you'll need to undo this later
    context.get_value(key)          read a key from the CURRENT context --
                                     callable from anywhere, no parameter needed
    context.detach(token)           restores whatever was current before attach

    context.set_value(key, value)
         │  (a plain function call -- returns a new Context, changes nothing yet)
         ▼
    context.attach(new_ctx)              <- start_as_current_span() does
         │   makes it current, returns      exactly this, using the SPAN
         │   a Token                        itself as the value
         ▼
    ...any code below, even nested function calls with
    no parameters passed, can read it:
    context.get_value(key)
         │
         ▼
    context.detach(token)                <- closing the `with` block does
         restores the PREVIOUS context      exactly this
         (not an empty one -- whatever
          was current before attach)

PART 1 proves this using a real span: `start_as_current_span` is nothing
more than "attach a context with this span as the value." PART 2 uses the
raw primitives directly, with your OWN value instead of a span -- proving
Context is a general mechanism, not something span-specific.

Run:  uv run python 06_context.py
"""

from opentelemetry import context, trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("lesson-06")


# ------------------------------------------------- 1. a span IS a context value
print("=== part 1: what start_as_current_span actually does ===")
print("context BEFORE any span:", dict(context.get_current()))

with tracer.start_as_current_span("say-hello"):
    current = dict(context.get_current())
    print("context DURING the span:", current)
    print("(one key, and its value is literally the Span object)")

print("context AFTER the span ends:", dict(context.get_current()))
print("(empty again -- closing the `with` block called context.detach() for you)")


# --------------------------------------------- 2. the same mechanism, your own value
print("\n=== part 2: the raw primitives, with a value that isn't a span ===")

user_id_key = context.create_key("user-id")
print("before:", context.get_value(user_id_key))

new_ctx = context.set_value(user_id_key, "ada-123")      # a NEW Context -- nothing changed yet
print("set_value alone changes nothing:", context.get_value(user_id_key))

token = context.attach(new_ctx)                            # NOW it's current
print("after attach:", context.get_value(user_id_key))


def deep_function() -> None:
    """No user_id parameter anywhere -- it reads the ambient context instead."""
    print("  deep_function(), no params passed, still sees:", context.get_value(user_id_key))


deep_function()

context.detach(token)                                       # restore what came before
print("after detach:", context.get_value(user_id_key))

# Expected output:
#
# === part 1: what start_as_current_span actually does ===
# context BEFORE any span: {}
# context DURING the span: {'current-span-<uuid>': _Span(name="say-hello", ...)}
# (one key, and its value is literally the Span object)
# {
#     "name": "say-hello", ...                 <- printed HERE: the `with` block just
# }                                                exited, so SimpleSpanProcessor exported
#                                                   it immediately (same as lesson 01)
# context AFTER the span ends: {}
# (empty again -- closing the `with` block called context.detach() for you)
#
# === part 2: the raw primitives, with a value that isn't a span ===
# before: None
# set_value alone changes nothing: None
# after attach: ada-123
#   deep_function(), no params passed, still sees: ada-123
# after detach: None
