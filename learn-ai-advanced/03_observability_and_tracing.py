"""Lesson 03 -- Observability: Tracing, Token/Cost Tracking, Latency
========================================================================

WHY THIS MATTERS:
  Lesson 17 in learn-mcp built agent handoffs; lesson 13 in learn-langgraph
  built a StateGraph orchestrator. Neither answers the question you get
  asked in production: "why did this request take 4 seconds," "which tool
  call cost the most tokens," or "which step actually failed." Checkpointers
  (learn-langgraph lesson 08) save *state* so a graph can resume. Tracing
  is different: it records *what happened and when*, across every agent
  and tool call, into a tree you can inspect after the fact. Production
  systems use LangSmith or OpenTelemetry for this; this lesson builds the
  same tree by hand so the concept is visible before you adopt a tool
  that hides it.

WHAT YOU'LL LEARN:
  1. Spans: a named, timed unit of work (one tool call, one LLM call, one
     agent step) with a start time, end time, and optional parent
  2. Building a trace tree: child spans nest under the span that created
     them -- exactly the call structure of lesson 16's supervisor/
     specialist agents, but recorded instead of just printed
  3. Token and cost tracking: attaching metadata (tokens in/out, estimated
     cost) to a span so you can answer "which call was expensive"
  4. Latency waterfalls: rendering a trace tree so you can see which span
     dominated total request time
  5. Errors in a trace: a failed span shouldn't disappear -- it should
     show up in the tree with its error, same as lesson 12's non-fatal
     MCP-to-MCP failures

Concepts:
  - Span: {name, start_time, end_time, parent_id, attributes, error}
  - Trace: a tree of spans sharing one root -- one user request end-to-end
  - Waterfall: a visualization where each span's bar starts at its
    start_time and its width is its duration, nested under its parent
  - Attributes: arbitrary key/value metadata on a span (tokens, cost,
    tool name, args) -- what you'd filter/aggregate on in a real APM tool
  - Critical path: the longest chain of sequential spans -- the thing you
    have to speed up if you want the whole request faster (parallel
    branches off the critical path don't matter as much)

Flow:
  with tracer.span("handle_request") as root:       <- one trace, one root
      with tracer.span("supervisor", parent=root):
          ...
      with tracer.span("research_agent", parent=root):
          with tracer.span("search_web_tool", parent=research_agent):
              ...  <- attributes: tokens=0 (no LLM), latency=12ms
      with tracer.span("writer_agent", parent=root):
          with tracer.span("llm_call", parent=writer_agent):
              ...  <- attributes: tokens_in=120, tokens_out=40, cost=$0.0012

  Rendered waterfall (each span's bar positioned + sized by its timing):
    handle_request        [======================================] 145ms
      supervisor           [==]                                     8ms
      research_agent         [========]                            32ms
        search_web_tool         [======]                           24ms
      writer_agent                      [==============]           95ms
        llm_call                          [============]           88ms

  Maps to (production shape, not this repo's code):
    LangSmith / OpenTelemetry traces around langgraph_mcp_orchestrator.py
    -- each StateGraph node and each MCP tool call becomes one span,
    nested under the request's root span.

PREREQUISITES: Lesson 17 in learn-mcp (agent/tool call shape this traces)

Run:  uv run python 03_observability_and_tracing.py

EXPECTED OUTPUT:
  === Running a traced request ===
    (spans recorded silently as the request executes)

  === Trace tree ===
    handle_request                                   145ms
      supervisor                                        8ms
      research_agent                                   32ms
        search_web_tool                                24ms  tokens=0
      writer_agent                                      95ms
        llm_call                                        88ms  tokens_in=120 tokens_out=40 cost=$0.0012

  === Waterfall ===
    (ASCII bars positioned by start time, sized by duration)

  === Aggregates ===
    Total tokens: 160  |  Total cost: $0.001200  |  Total latency: 145ms
    Critical path (longest chain): handle_request -> writer_agent -> llm_call

  === Error span demo ===
    A failing tool call still appears in the trace, marked ERROR, instead
    of vanishing -- same non-fatal-but-visible pattern as MCP-to-MCP (L15)
"""

import asyncio
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field


# ============================================================================
# STEP 1: Spans and the Tracer
# ============================================================================

@dataclass
class Span:
    id: str
    name: str
    parent_id: str | None
    start: float
    end: float | None = None
    attributes: dict = field(default_factory=dict)
    error: str | None = None

    @property
    def duration_ms(self) -> float:
        end = self.end if self.end is not None else time.monotonic()
        return (end - self.start) * 1000


class Tracer:
    """Records spans into a flat list; the parent_id links reconstruct the
    tree. A real tracer (OpenTelemetry SDK) does the same thing, plus
    exporting to a backend (LangSmith, Jaeger, Honeycomb) instead of
    keeping everything in memory."""

    def __init__(self):
        self.spans: list[Span] = []
        self._stack: list[str] = []  # current span id stack, for auto-parenting

    @contextmanager
    def span(self, name: str, **attributes):
        parent_id = self._stack[-1] if self._stack else None
        span = Span(id=str(uuid.uuid4())[:8], name=name, parent_id=parent_id,
                    start=time.monotonic(), attributes=dict(attributes))
        self.spans.append(span)
        self._stack.append(span.id)
        try:
            yield span
        except Exception as e:
            span.error = str(e)
            raise
        finally:
            span.end = time.monotonic()
            self._stack.pop()

    def root_spans(self) -> list[Span]:
        return [s for s in self.spans if s.parent_id is None]

    def children_of(self, span_id: str) -> list[Span]:
        return [s for s in self.spans if s.parent_id == span_id]


# ============================================================================
# STEP 2: A traced request -- reuses the agent shape from learn-mcp lesson 17
# ============================================================================
# search_web and the LLM call are simulated with time.sleep so the demo has
# real, varying durations to show in the waterfall -- no network, no LLM
# call needed to see how tracing works.

async def traced_request(tracer: Tracer, query: str):
    with tracer.span("handle_request", query=query):
        with tracer.span("supervisor"):
            await asyncio.sleep(0.008)

        with tracer.span("research_agent"):
            with tracer.span("search_web_tool") as tool_span:
                await asyncio.sleep(0.024)
                tool_span.attributes["tokens"] = 0  # no LLM in this tool

        with tracer.span("writer_agent"):
            with tracer.span("llm_call") as llm_span:
                await asyncio.sleep(0.088)
                tokens_in, tokens_out = 120, 40
                # Rough GPT-4o-class pricing for illustration, not a real quote.
                cost = tokens_in * 0.000005 + tokens_out * 0.000015
                llm_span.attributes.update(
                    tokens_in=tokens_in, tokens_out=tokens_out, cost=round(cost, 6)
                )


# ============================================================================
# STEP 3: Rendering the trace tree and a waterfall
# ============================================================================

def render_tree(tracer: Tracer, span: Span, depth: int = 0, out: list[str] | None = None) -> list[str]:
    if out is None:
        out = []
    indent = "  " * depth
    attrs = " ".join(f"{k}={v}" for k, v in span.attributes.items() if k not in ("query",))
    error_tag = "  [ERROR]" if span.error else ""
    line = f"    {indent}{span.name:<28}{span.duration_ms:6.0f}ms  {attrs}{error_tag}"
    out.append(line)
    for child in tracer.children_of(span.id):
        render_tree(tracer, child, depth + 1, out)
    return out


def render_waterfall(tracer: Tracer, root: Span, width: int = 40) -> list[str]:
    total = root.duration_ms or 1.0
    out = []

    def walk(span: Span, depth: int):
        offset = (span.start - root.start) * 1000
        bar_start = round((offset / total) * width)
        bar_len = max(1, round((span.duration_ms / total) * width))
        bar = " " * bar_start + "[" + "=" * bar_len + "]"
        out.append(f"    {'  ' * depth}{span.name:<20}{bar:<{width + 2}} {span.duration_ms:.0f}ms")
        for child in tracer.children_of(span.id):
            walk(child, depth + 1)

    walk(root, 0)
    return out


def critical_path(tracer: Tracer, span: Span) -> list[str]:
    """The chain of spans that dominates total latency: at each level,
    follow the child with the longest duration. Speeding up anything NOT
    on this path won't make the overall request faster."""
    path = [span.name]
    children = tracer.children_of(span.id)
    if children:
        slowest = max(children, key=lambda c: c.duration_ms)
        path += critical_path(tracer, slowest)
    return path


# ============================================================================
# STEP 4: Errors stay visible in the trace
# ============================================================================

async def traced_request_with_failure(tracer: Tracer):
    with tracer.span("handle_request_2"):
        with tracer.span("research_agent"):
            try:
                with tracer.span("search_web_tool"):
                    await asyncio.sleep(0.005)
                    raise ConnectionError("search index unreachable")
            except ConnectionError:
                pass  # non-fatal: caller degrades gracefully, but span kept the error


# ============================================================================
# Demo
# ============================================================================

async def main():
    tracer = Tracer()

    print("=== Running a traced request ===")
    await traced_request(tracer, "quarterly earnings")
    print("    (spans recorded silently as the request executed)")
    print()

    print("=== Trace tree ===")
    root = tracer.root_spans()[0]
    for line in render_tree(tracer, root):
        print(line)
    print()

    print("=== Waterfall ===")
    for line in render_waterfall(tracer, root):
        print(line)
    print()

    print("=== Aggregates ===")
    total_tokens = sum(
        s.attributes.get("tokens_in", 0) + s.attributes.get("tokens_out", 0) + s.attributes.get("tokens", 0)
        for s in tracer.spans
    )
    total_cost = sum(s.attributes.get("cost", 0) for s in tracer.spans)
    path = " -> ".join(critical_path(tracer, root))
    print(f"    Total tokens: {total_tokens}  |  Total cost: ${total_cost:.6f}  |  Total latency: {root.duration_ms:.0f}ms")
    print(f"    Critical path (longest chain): {path}")
    print()

    print("=== Error span demo ===")
    tracer2 = Tracer()
    await traced_request_with_failure(tracer2)
    for line in render_tree(tracer2, tracer2.root_spans()[0]):
        print(line)
    print("    A failing tool call still appears in the trace, marked [ERROR],")
    print("    instead of vanishing -- same non-fatal-but-visible pattern as")
    print("    MCP-to-MCP's try/except (learn-mcp lesson 16).")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Tracing answers questions checkpointing and logging don't:
    #   - Checkpointers (learn-langgraph L08) save STATE so a graph can
    #     resume after an interrupt -- they don't tell you what was slow.
    #   - Plain logs tell you an event happened, but not how it nests inside
    #     the rest of the request, or how long each piece took relative to
    #     its siblings.
    #   - A trace tree gives you both: structure (what called what) AND
    #     timing (how long each piece took) AND cost (tokens/dollars per
    #     span) in one artifact you can render as a waterfall.
    #
    # The critical path matters more than it looks: in this demo,
    # optimizing search_web_tool (24ms) barely moves total latency (145ms)
    # because llm_call (88ms) dominates -- that's the one worth speeding up
    # (smaller prompt, cheaper model, streaming) if the request feels slow.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a second LLM call in parallel with search_web_tool (asyncio.gather)
    #    and confirm the waterfall shows overlapping bars, not sequential ones.
    # 2. Add a `tracer.spans_by_name("llm_call")` helper and sum cost across
    #    multiple requests -- the start of a per-day cost dashboard.
    # 3. Export `tracer.spans` to JSON and sketch what a `POST /traces`
    #    endpoint accepting this shape would look like (this is roughly
    #    what OpenTelemetry's OTLP exporter sends).
    # 4. Wrap lesson 16's SupervisorAgent.run_delegation() with tracer.span()
    #    calls around each specialist call and render the resulting tree.
