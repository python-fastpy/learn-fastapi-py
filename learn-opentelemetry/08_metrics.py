"""Lesson 08 -- Metrics: the second OTel pillar
==================================================

Traces (lessons 01-07) answer "what happened in THIS one request?".
Metrics answer a different question: "how many, how long, how much, RIGHT
NOW?" -- aggregated numbers, not individual events.

THREE INSTRUMENT KINDS (there are more; these three cover most real use)

    Counter          only ever goes UP           requests served, errors seen
    Histogram        records a DISTRIBUTION      request duration, payload size
    UpDownCounter    goes up AND down            active connections, queue depth

`MeterProvider`/`Meter` are metrics' counterparts to `TracerProvider`/
`Tracer`. The big mechanical difference from every earlier lesson: a span
exports the INSTANT it ends. A metric does not -- `.add()`/`.record()`
just update an in-memory aggregate. Nothing is exported until a
MetricReader pulls a snapshot, on a timer:

    meter.create_counter(...) / create_histogram(...) / create_up_down_counter(...)
         │  .add(n, {attrs})   or   .record(value, {attrs})
         ▼
    aggregated IN MEMORY, one running total per distinct set of attributes
    (two counter.add(1, {"language": "en"}) calls become ONE data point: 2)
         │
         ▼
    PeriodicExportingMetricReader    pulls the current snapshot every
                                       export_interval_millis (default 60s) --
                                       or immediately, if you call
                                       provider.shutdown() / force_flush()
         │
         ▼
    MetricExporter    hands the snapshot to wherever it goes
                       (ConsoleMetricExporter, OTLPMetricExporter, ...)

This lesson uses a tiny custom exporter instead of the real
ConsoleMetricExporter, purely to keep the printed output readable --
the real one dumps the full OTLP-shaped JSON (bucket boundaries, start/end
timestamps, resource attributes, the works), which is accurate but a lot
to read for a first lesson. Swap it in yourself to see the real shape.

Run:  uv run python 08_metrics.py
"""

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    MetricExporter,
    MetricExportResult,
    PeriodicExportingMetricReader,
)


class SummaryMetricExporter(MetricExporter):
    """One readable line per data point, instead of ConsoleMetricExporter's
    full JSON. Real exporters (Console, OTLP, ...) implement this same
    three-method interface."""

    def export(self, metrics_data, timeout_millis: float = 10000, **kwargs) -> MetricExportResult:
        for resource_metrics in metrics_data.resource_metrics:
            for scope_metrics in resource_metrics.scope_metrics:
                for metric in scope_metrics.metrics:
                    for point in metric.data.data_points:
                        value = getattr(point, "value", None)
                        if value is None:                     # a Histogram has no .value
                            value = f"count={point.count} sum={point.sum}"
                        print(f"  {metric.name}{dict(point.attributes)} = {value}")
        return MetricExportResult.SUCCESS

    def shutdown(self, timeout_millis: float = 30000, **kwargs) -> None:
        pass

    def force_flush(self, timeout_millis: float = 10000) -> bool:
        return True


# export_interval_millis is set absurdly long on purpose -- this lesson
# forces one export itself, at the very end, via provider.shutdown()
reader = PeriodicExportingMetricReader(SummaryMetricExporter(), export_interval_millis=60_000)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter("lesson-08")

# ------------------------------------------------------------------- Counter
greetings_count = meter.create_counter("greetings.count", description="how many greetings sent")
greetings_count.add(1, {"language": "en"})
greetings_count.add(2, {"language": "en"})      # same attributes -> SUMS with the line above
greetings_count.add(1, {"language": "fr"})       # different attributes -> its own data point

# ----------------------------------------------------------------- Histogram
greeting_duration = meter.create_histogram("greeting.duration", unit="ms")
greeting_duration.record(12.3, {"language": "en"})
greeting_duration.record(45.6, {"language": "en"})   # becomes count=2, sum=57.9, min/max tracked

# -------------------------------------------------------------- UpDownCounter
active_greetings = meter.create_up_down_counter("active.greetings")
active_greetings.add(1)     # a greeting starts
active_greetings.add(1)     # another one starts
active_greetings.add(-1)    # the first one finishes -- net value settles at 1

print("nothing has been exported yet -- it's all just in-memory aggregates\n")
print("forcing one export now, via provider.shutdown():")
provider.shutdown()

# Expected output:
#
# nothing has been exported yet -- it's all just in-memory aggregates
#
# forcing one export now, via provider.shutdown():
#   greetings.count{'language': 'en'} = 3
#   greetings.count{'language': 'fr'} = 1
#   greeting.duration{'language': 'en'} = count=2 sum=57.900000000000006
#   active.greetings{} = 1
#
# Notice greetings.count{'language': 'en'} is 3, not two separate lines
# of 1 and 2 -- that's the aggregation: same instrument, same attributes,
# one running total.
