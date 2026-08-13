import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from intellipay.config import Settings
from intellipay.model_pricing import ReasoningCostReport
from intellipay.workflow.models import ReviewEvent
from intellipay.workflow.storage import SQLiteStore

REDACTED_KEYS = {"actor", "payment_id", "rationale"}


def event_envelope(event: ReviewEvent) -> dict[str, Any]:
    return {
        "schema_version": event.schema_version,
        "sequence": event.sequence,
        "event_id": event.event_id,
        "event_type": event.event_type.replace("_", "."),
        "occurred_at": event.created_at,
        "trace_id": event.trace_id,
        "span_id": event.span_id,
        "data": {
            key: "[REDACTED]" if key in REDACTED_KEYS else value
            for key, value in event.payload.items()
        },
    }


def export_events(store: SQLiteStore, *, after_sequence: int = 0) -> str:
    return "".join(
        json.dumps(event_envelope(event), sort_keys=True) + "\n"
        for event in store.events_after(after_sequence)
    )


def export_events_markdown(
    store: SQLiteStore,
    *,
    reasoning_cost: ReasoningCostReport,
    after_sequence: int = 0,
) -> str:
    events = [event_envelope(event) for event in store.events_after(after_sequence)]
    event_counts = Counter(event["event_type"] for event in events)
    usage_basis = (
        "Estimated local usage"
        if reasoning_cost.estimated_usage_calls and not reasoning_cost.exact_usage_calls
        else "Provider-reported usage"
        if reasoning_cost.exact_usage_calls and not reasoning_cost.estimated_usage_calls
        else "Mixed exact and estimated usage"
    )
    lines = [
        "# IntelliPay Observability Report",
        "",
        "This report contains the redacted durable events captured during invoice processing.",
        "",
        "## Summary",
        "",
        f"- Total events: {len(events)}",
        f"- Sequence range: {events[0]['sequence']} to {events[-1]['sequence']}"
        if events
        else "- Sequence range: none",
        "",
        "## Reasoning Usage and Estimated Cost",
        "",
        f"- Usage basis: {usage_basis}",
        f"- Reasoning calls: {reasoning_cost.calls}",
        f"- Input tokens: {reasoning_cost.input_tokens}",
        f"- Cached input tokens: {reasoning_cost.cached_input_tokens}",
        f"- Output tokens: {reasoning_cost.output_tokens}",
        f"- Estimated API cost: ${reasoning_cost.estimated_cost_usd:.6f} {reasoning_cost.currency}",
        f"- Pricing effective date: {reasoning_cost.pricing_effective_date}",
        f"- Pricing source: {reasoning_cost.pricing_source_url}",
        f"- Unpriced metered calls: {reasoning_cost.unpriced_calls}",
        "",
        "| Operation | Calls | Input tokens | Cached input | Output tokens | Estimated cost |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        *(
            f"| `{item.operation}` | {item.calls} | {item.input_tokens} | "
            f"{item.cached_input_tokens} | {item.output_tokens} | "
            f"${item.estimated_cost_usd:.6f} {reasoning_cost.currency} |"
            for item in reasoning_cost.by_operation
        ),
        "",
        "## Event Types",
        "",
        "| Event type | Count |",
        "| --- | ---: |",
        *(f"| `{event_type}` | {count} |" for event_type, count in sorted(event_counts.items())),
        "",
        "## Captured Events",
        "",
        "| Sequence | Occurred at | Event type | Redacted data |",
        "| ---: | --- | --- | --- |",
    ]
    for event in events:
        data = json.dumps(event["data"], sort_keys=True).replace("|", "\\|")
        lines.append(
            f"| {event['sequence']} | {event['occurred_at']} | `{event['event_type']}` | `{data}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export versioned IntelliPay events as JSONL")
    parser.add_argument("--database-path", type=Path, default=None)
    parser.add_argument("--after-sequence", type=int, default=0)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    overrides = {"database_path": args.database_path} if args.database_path else {}
    store = SQLiteStore(Settings(**overrides).database_path)
    output = export_events(store, after_sequence=args.after_sequence)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    else:
        print(output, end="")
