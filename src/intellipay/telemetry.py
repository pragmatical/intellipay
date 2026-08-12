from collections.abc import Iterator, Mapping
from contextlib import contextmanager

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import Meter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import Span, Status, StatusCode, Tracer

from intellipay.config import Settings

AttributeValue = str | bool | int | float


class Telemetry:
    def __init__(
        self,
        tracer: Tracer,
        meter: Meter,
        *,
        tracer_provider: TracerProvider | None = None,
        meter_provider: MeterProvider | None = None,
    ) -> None:
        self._tracer = tracer
        self._tracer_provider = tracer_provider
        self._meter_provider = meter_provider
        self._runs = meter.create_counter("intellipay.runs")
        self._run_duration = meter.create_histogram("intellipay.run.duration", unit="ms")
        self._node_duration = meter.create_histogram("intellipay.node.duration", unit="ms")
        self._reasoning_calls = meter.create_counter("intellipay.reasoning.calls")
        self._reasoning_duration = meter.create_histogram(
            "intellipay.reasoning.duration", unit="ms"
        )
        self._payments = meter.create_counter("intellipay.payments")

    @contextmanager
    def span(
        self,
        name: str,
        attributes: Mapping[str, AttributeValue] | None = None,
        non_error_exceptions: tuple[type[BaseException], ...] = (),
    ) -> Iterator[Span]:
        with self._tracer.start_as_current_span(
            name,
            attributes=attributes,
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            try:
                yield span
            except Exception as error:
                if isinstance(error, non_error_exceptions):
                    raise
                span.add_event(
                    "exception",
                    {"exception.type": f"{type(error).__module__}.{type(error).__qualname__}"},
                )
                span.set_status(Status(StatusCode.ERROR, type(error).__name__))
                raise

    def record_run(self, *, outcome: str, reasoning_mode: str, duration_ms: float) -> None:
        attributes = {
            "intellipay.route.outcome": outcome,
            "intellipay.reasoning.mode": reasoning_mode,
        }
        self._runs.add(1, attributes)
        self._run_duration.record(duration_ms, attributes)

    def record_node(self, *, node: str, status: str, duration_ms: float) -> None:
        self._node_duration.record(
            duration_ms,
            {"intellipay.graph.node": node, "intellipay.operation.status": status},
        )

    def record_reasoning(
        self,
        *,
        operation: str,
        provider: str,
        status: str,
        duration_ms: float,
    ) -> None:
        attributes = {
            "gen_ai.operation.name": operation,
            "gen_ai.system": provider,
            "intellipay.operation.status": status,
        }
        self._reasoning_calls.add(1, attributes)
        self._reasoning_duration.record(duration_ms, attributes)

    def record_payment(self, *, status: str, replayed: bool) -> None:
        self._payments.add(
            1,
            {"intellipay.payment.status": status, "intellipay.payment.replayed": replayed},
        )

    def force_flush(self, timeout_millis: int = 5_000) -> bool:
        trace_flushed = self._tracer_provider is None or self._tracer_provider.force_flush(
            timeout_millis=timeout_millis
        )
        metric_flushed = self._meter_provider is None or self._meter_provider.force_flush(
            timeout_millis=timeout_millis
        )
        return trace_flushed and metric_flushed

    def shutdown(self) -> None:
        if self._tracer_provider is not None:
            self._tracer_provider.shutdown()
        if self._meter_provider is not None:
            self._meter_provider.shutdown()


def create_telemetry(
    settings: Settings,
    *,
    span_exporter: SpanExporter | None = None,
    metric_exporter: MetricExporter | None = None,
) -> Telemetry:
    if not settings.telemetry_enabled and span_exporter is None and metric_exporter is None:
        return Telemetry(trace.get_tracer("intellipay"), metrics.get_meter("intellipay"))

    resource = Resource.create(
        {
            "service.name": settings.telemetry_service_name,
            "service.version": "0.1.0",
            "deployment.environment.name": settings.telemetry_environment,
        }
    )
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=ParentBased(TraceIdRatioBased(settings.telemetry_sample_ratio)),
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter or OTLPSpanExporter()))

    reader = PeriodicExportingMetricReader(metric_exporter or OTLPMetricExporter())
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    return Telemetry(
        tracer_provider.get_tracer("intellipay"),
        meter_provider.get_meter("intellipay"),
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
    )
