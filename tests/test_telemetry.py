from pathlib import Path

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from intellipay.config import Settings
from intellipay.event_export import export_events
from intellipay.reasoning.local import LocalReasoningProvider
from intellipay.reasoning.models import ExtractionRequest
from intellipay.telemetry import Telemetry
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.models import Outcome, PaymentStatus
from intellipay.workflow.storage import SQLiteStore


def ambiguous_invoice(tmp_path: Path) -> Path:
    path = tmp_path / "ambiguous.txt"
    content = (
        Path("data/invoices/invoice_1001.txt").read_text().replace("$5,000.00", "$5,OOO.OO", 1)
    )
    path.write_text(content)
    return path


class SensitiveOutageProvider(LocalReasoningProvider):
    def extract_invoice(self, request: ExtractionRequest):
        raise TimeoutError("sensitive provider response must not be exported")


class RejectingSpanExporter(SpanExporter):
    def __init__(self) -> None:
        self.export_count = 0

    def export(self, spans):
        self.export_count += len(spans)
        return SpanExportResult.FAILURE


def test_workflow_emits_correlated_spans_and_metrics(tmp_path: Path) -> None:
    span_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    metric_reader = InMemoryMetricReader()
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    telemetry = Telemetry(
        tracer_provider.get_tracer("intellipay-test"),
        meter_provider.get_meter("intellipay-test"),
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
    )

    database = tmp_path / "telemetry.db"
    result = InvoiceWorkflow(
        Settings(database_path=database, _env_file=None),
        telemetry=telemetry,
    ).process(Path("data/invoices/invoice_1001.txt"))
    telemetry.force_flush()

    spans = span_exporter.get_finished_spans()
    root = next(span for span in spans if span.name == "intellipay.invoice.process")
    node_spans = [span for span in spans if span.name.startswith("intellipay.node.")]
    assert root.attributes["intellipay.run.id"] == result.run_id
    assert root.attributes["intellipay.route.outcome"] == "APPROVE"
    assert {span.name for span in node_spans} == {
        "intellipay.node.extract",
        "intellipay.node.validate",
        "intellipay.node.decide",
        "intellipay.node.critique_decision",
        "intellipay.node.authorize_payment",
        "intellipay.node.pay",
    }
    assert all(span.parent and span.parent.span_id == root.context.span_id for span in node_spans)
    assert all(span.attributes["intellipay.run.id"] == result.run_id for span in node_spans)

    metrics_data = metric_reader.get_metrics_data()
    metric_names = {
        metric.name
        for resource_metric in metrics_data.resource_metrics
        for scope_metric in resource_metric.scope_metrics
        for metric in scope_metric.metrics
    }
    assert {
        "intellipay.runs",
        "intellipay.run.duration",
        "intellipay.node.duration",
        "intellipay.payments",
    } <= metric_names

    events = SQLiteStore(database).events(result.run_id)
    assert all(event.event_id.startswith("evt_") for event in events)
    assert all(event.trace_id == f"{root.context.trace_id:032x}" for event in events)
    exported = export_events(SQLiteStore(database))
    assert result.run_id not in exported
    assert '"event_type": "workflow.completed"' in exported
    assert '"trace_id":' in exported


def test_reasoning_spans_are_nested_and_redacted(tmp_path: Path) -> None:
    span_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    metric_reader = InMemoryMetricReader()
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    telemetry = Telemetry(
        tracer_provider.get_tracer("intellipay-test"),
        meter_provider.get_meter("intellipay-test"),
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
    )

    result = InvoiceWorkflow(
        Settings(database_path=tmp_path / "reasoning-telemetry.db", _env_file=None),
        telemetry=telemetry,
    ).process(ambiguous_invoice(tmp_path))

    spans = span_exporter.get_finished_spans()
    reasoning_spans = [span for span in spans if span.name.startswith("intellipay.reasoning.")]
    node_span_ids = {
        span.context.span_id for span in spans if span.name.startswith("intellipay.node.")
    }
    assert [span.name for span in reasoning_spans] == [
        "intellipay.reasoning.extract",
        "intellipay.reasoning.critique_extraction",
        "intellipay.reasoning.repair_extraction",
    ]
    assert all(span.parent and span.parent.span_id in node_span_ids for span in reasoning_spans)
    assert all(span.attributes["intellipay.run.id"] == result.run_id for span in reasoning_spans)
    serialized_attributes = repr([span.attributes for span in reasoning_spans])
    assert "ACME" not in serialized_attributes
    assert "WidgetA" not in serialized_attributes
    assert "5,OOO" not in serialized_attributes
    telemetry.force_flush()
    metric_names = {
        metric.name
        for resource_metric in metric_reader.get_metrics_data().resource_metrics
        for scope_metric in resource_metric.scope_metrics
        for metric in scope_metric.metrics
    }
    assert {
        "intellipay.reasoning.calls",
        "intellipay.reasoning.tokens",
        "intellipay.reasoning.estimated_cost",
    } <= metric_names


def test_provider_error_text_is_redacted_from_spans(tmp_path: Path) -> None:
    span_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    telemetry = Telemetry(
        tracer_provider.get_tracer("intellipay-test"),
        MeterProvider().get_meter("intellipay-test"),
        tracer_provider=tracer_provider,
    )

    result = InvoiceWorkflow(
        Settings(database_path=tmp_path / "error-telemetry.db", _env_file=None),
        provider=SensitiveOutageProvider(),
        telemetry=telemetry,
    ).process(ambiguous_invoice(tmp_path))

    assert result.outcome is Outcome.ESCALATE
    assert "sensitive provider response" not in repr(span_exporter.get_finished_spans())
    error_spans = [span for span in span_exporter.get_finished_spans() if not span.status.is_ok]
    assert error_spans
    assert all(
        event.attributes["exception.type"] == "builtins.TimeoutError"
        for span in error_spans
        for event in span.events
        if event.name == "exception"
    )


def test_exporter_failure_cannot_change_payment_result(tmp_path: Path) -> None:
    span_exporter = RejectingSpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    telemetry = Telemetry(
        tracer_provider.get_tracer("intellipay-test"),
        MeterProvider().get_meter("intellipay-test"),
        tracer_provider=tracer_provider,
    )

    result = InvoiceWorkflow(
        Settings(database_path=tmp_path / "exporter-failure.db", _env_file=None),
        telemetry=telemetry,
    ).process(Path("data/invoices/invoice_1001.txt"))

    assert span_exporter.export_count > 0
    assert result.outcome is Outcome.APPROVE
    assert result.payment_status is PaymentStatus.SUCCESS
    assert SQLiteStore(tmp_path / "exporter-failure.db").payment_count() == 1
