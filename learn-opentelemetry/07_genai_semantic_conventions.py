"""Lesson 07 -- GenAI semantic conventions, and how a backend maps them
===========================================================================

Every earlier lesson used attribute names you made up yourself
("greet.name", "request.id", ...). For an LLM call, OpenTelemetry defines
a STANDARD set of attribute names instead -- the `gen_ai.*` semantic
conventions. Use them, and any backend that understands the convention
(Braintrust, Datadog LLM Observability, Honeycomb, ...) can render a rich
"this was an LLM call, here's the model/tokens/cost" view with ZERO custom
mapping code on your side.

    span name          "{gen_ai.operation.name} {gen_ai.request.model}"
                        e.g. "chat claude-sonnet-5" -- a convention too,
                        not required, but what most tooling expects

    gen_ai.operation.name    "chat" | "execute_tool" | ...  -- what kind of call
    gen_ai.provider.name     "anthropic" | "openai" | ...
    gen_ai.request.model     the model you ASKED for
    gen_ai.response.model    the model that actually ANSWERED (can differ)
    gen_ai.usage.input_tokens / gen_ai.usage.output_tokens

These are just span attributes -- same `span.set_attribute(...)` call every
earlier lesson used. Nothing new mechanically; what's new is that the
NAMES are standardized, so a backend can recognize them.

PART 2 OF THIS LESSON IS REFERENCE ONLY (not re-verified here against a
live account -- it documents what Braintrust's own docs say): how one
real backend, Braintrust, maps these standard names onto its own fields.

DOCUMENTATION
    OTel GenAI attribute registry -- EVERY gen_ai.* field, with type,
    description and examples (request/response/usage/agent/tool/workflow/
    embeddings/retrieval/evaluation/...). The registry moved out of the
    main semantic-conventions repo into its own; the old opentelemetry.io
    URL below is now a deprecated stub that just redirects -- use the
    GitHub one, it's the current source of truth:
        https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/registry/attributes/gen-ai.md
        (deprecated redirect: https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)
    OTel GenAI spans spec (which fields are REQUIRED/RECOMMENDED per span
    type -- "inference", "execute_tool", "invoke_agent", ...):
        https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md
    Braintrust's OpenTelemetry integration (the mapping table in Part 2):
        https://www.braintrust.dev/docs/integrations/sdk-integrations/opentelemetry
    Braintrust's longer guide on OTel LLM tracing:
        https://www.braintrust.dev/articles/opentelemetry-llm-tracing-guide

Run:  uv run python 07_genai_semantic_conventions.py
"""

import time

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)


def call_llm(prompt: str) -> str:
    """Stands in for a real client.messages.create(...) call."""
    time.sleep(0.05)
    return "The capital of France is Paris."


model = "claude-sonnet-5"

# span name convention: "{gen_ai.operation.name} {gen_ai.request.model}"
with tracer.start_as_current_span(f"chat {model}") as span:
    prompt = "What is the capital of France?"

    span.set_attribute("gen_ai.operation.name", "chat")
    span.set_attribute("gen_ai.provider.name", "anthropic")
    span.set_attribute("gen_ai.request.model", model)

    response = call_llm(prompt)

    span.set_attribute("gen_ai.response.model", model)
    span.set_attribute("gen_ai.usage.input_tokens", 8)
    span.set_attribute("gen_ai.usage.output_tokens", 7)

    print(response)


# =============================================================================
# PART 2 (reference): how Braintrust maps gen_ai.* onto its own fields
# =============================================================================
#
# Braintrust's ingest auto-recognizes gen_ai.* attributes and rewrites them
# onto its own schema -- you don't write any mapping code, this happens on
# their side purely because you used the standard names:
#
#   your span attribute                     Braintrust field
#   ---------------------------------------  ---------------------------------
#   gen_ai.input.messages                    input
#   gen_ai.output.messages                   output
#   gen_ai.request.*  (model params)         metadata.*
#                                             (a provider prefix is stripped:
#                                              "openai/gpt-4o" -> "gpt-4o")
#   gen_ai.operation.name                    span_attributes.type
#                                             ("chat" -> "llm",
#                                              "execute_tool" -> "tool")
#   gen_ai.usage.*  (tokens, incl. cache)     metrics.*
#                                             (gen_ai.usage.prompt_tokens /
#                                              .completion_tokens are Braintrust's
#                                              PREFERRED names; .input_tokens /
#                                              .output_tokens -- used above -- are
#                                              an accepted alternative, normalized
#                                              to the same metrics fields)
#   gen_ai.agent.tools                       metadata.tools
#
# So for the exact span built above: gen_ai.operation.name="chat" would
# land in Braintrust as span_attributes.type="llm", and
# gen_ai.usage.input_tokens/output_tokens would populate its per-trace
# token metrics -- automatically.
#
# TO ACTUALLY SEND IT THERE: same OTLPSpanExporter class as lesson 03,
# just a different endpoint, an API key, and (per Braintrust's example)
# an x-bt-parent header naming which project the trace belongs to:
#
#     from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
#     exporter = OTLPSpanExporter(
#         endpoint="https://api.braintrust.dev/otel/v1/traces",
#         headers={
#             "Authorization": "Bearer <your Braintrust API key>",
#             "x-bt-parent": "project_id:<your project id>",
#         },
#     )
#     # or let the exporter pick up the endpoint from an env var instead:
#     #   OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://api.braintrust.dev/otel/v1/traces
#
# GOTCHA (from Braintrust's docs): their intake expects TRACES (spans),
# not OTel LOG records -- some tools emit GenAI data as logs instead of
# spans, and that would not map the way this lesson describes.
#
# ALTERNATIVE: Braintrust also has its own braintrust.* attribute
# namespace, for when you want direct control over input/output/scores
# instead of going through the gen_ai.* convention's mapping rules.

# Expected output (tokens/timestamps are fixed inputs here, not random --
# but start_time/end_time and the trace_id/span_id still vary per run):
#
# The capital of France is Paris.
# {
#     "name": "chat claude-sonnet-5",
#     "attributes": {
#         "gen_ai.operation.name": "chat",
#         "gen_ai.provider.name": "anthropic",
#         "gen_ai.request.model": "claude-sonnet-5",
#         "gen_ai.response.model": "claude-sonnet-5",
#         "gen_ai.usage.input_tokens": 8,
#         "gen_ai.usage.output_tokens": 7
#     },
#     ...
# }
