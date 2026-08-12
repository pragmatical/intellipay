import argparse
import json
from pathlib import Path
from typing import Any

from intellipay.config import Settings
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
