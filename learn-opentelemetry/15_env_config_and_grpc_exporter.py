"""Lesson 15 -- Zero-code config via OTEL_* env vars, and the gRPC exporter
===============================================================================

Two smaller, unrelated things that didn't earn their own lesson.

PART 1 (executable, verified below): most of lessons 01-04 can be
configured from the OUTSIDE, with no code changes, via standard `OTEL_*`
environment variables. `TracerProvider()` and friends read them when you
don't pass the equivalent constructor argument yourself:

    OTEL_SERVICE_NAME                fixes lesson 01's "unknown_service:python.exe"
                                      without touching code -- same job as lesson
                                      04's Resource.create({SERVICE_NAME: ...})
    OTEL_EXPORTER_OTLP_ENDPOINT       where lesson 03's OTLPSpanExporter sends spans,
                                      if you construct it with no endpoint= at all
    OTEL_TRACES_SAMPLER               "always_on" | "always_off" | "traceidratio" | ...
                                      -- picks lesson 13's sampler by name instead of code
    OTEL_RESOURCE_ATTRIBUTES          "key1=val1,key2=val2" -- extra Resource attributes

This is what makes auto-instrumentation (mentioned, not covered, when we
first discussed OTel's gaps) practical: point `opentelemetry-instrument`
at your app with these env vars set, and nothing in your source changes.

PART 2 (reference only -- NOT installed/run in this project; needs the
separate `opentelemetry-exporter-otlp-proto-grpc` package plus `grpcio`):
every OTLPSpanExporter used so far has been the HTTP/protobuf variant.
There's a gRPC variant too, same constructor shape, different port by
convention (4317 instead of HTTP's 4318):

    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    exporter = OTLPSpanExporter(endpoint="localhost:4317")   # note: no http:// prefix,
                                                                # and no /v1/traces suffix --
                                                                # gRPC addresses a host:port,
                                                                # not a URL path
    provider.add_span_processor(BatchSpanProcessor(exporter))

Pick HTTP when you want something that works through ordinary HTTP
infrastructure (proxies, load balancers, simple firewalls); pick gRPC
when your collector/backend prefers it and you don't need that simplicity
-- most backends, including the Collector itself, accept both on their
respective default ports at once.

Run:  uv run python 15_env_config_and_grpc_exporter.py
"""

import os
import subprocess
import sys

CHECK_SCRIPT = (
    "from opentelemetry.sdk.trace import TracerProvider\n"
    "provider = TracerProvider()\n"  # no resource= passed -- reads the env var instead
    "print(provider.resource.attributes.get('service.name'))\n"
)


def demo_env_var_service_name() -> None:
    """A SEPARATE process, so the env var is set before the SDK ever reads it
    (TracerProvider() only reads OTEL_SERVICE_NAME once, at construction)."""
    print("--- without OTEL_SERVICE_NAME set ---")
    default_env = {k: v for k, v in os.environ.items() if k != "OTEL_SERVICE_NAME"}
    result = subprocess.run([sys.executable, "-c", CHECK_SCRIPT], capture_output=True, text=True, env=default_env)
    print("service.name ->", result.stdout.strip())

    print("\n--- with OTEL_SERVICE_NAME=env-configured-service ---")
    env_with_var = {**default_env, "OTEL_SERVICE_NAME": "env-configured-service"}
    result = subprocess.run([sys.executable, "-c", CHECK_SCRIPT], capture_output=True, text=True, env=env_with_var)
    print("service.name ->", result.stdout.strip(), "  <- no code change, just an env var")


if __name__ == "__main__":
    demo_env_var_service_name()

# Expected output:
#
# --- without OTEL_SERVICE_NAME set ---
# service.name -> unknown_service:python.exe
#
# --- with OTEL_SERVICE_NAME=env-configured-service ---
# service.name -> env-configured-service   <- no code change, just an env var
