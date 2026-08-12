import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from opentelemetry import trace

from intellipay.reasoning.models import InvoiceCandidate
from intellipay.workflow.models import (
    Finding,
    Outcome,
    PaymentStatus,
    ReviewAction,
    ReviewEvent,
    ReviewTask,
)

MIGRATIONS = (
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS inventory (
            item TEXT PRIMARY KEY,
            available_quantity TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            source_hash TEXT NOT NULL,
            invoice_number TEXT,
            reasoning_mode TEXT NOT NULL,
            outcome TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL REFERENCES runs(run_id),
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payments (
            idempotency_key TEXT PRIMARY KEY,
            payment_id TEXT NOT NULL UNIQUE,
            invoice_number TEXT NOT NULL,
            amount TEXT NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """,
    ),
    (
        2,
        """
        ALTER TABLE runs ADD COLUMN invoice_fingerprint TEXT;
        CREATE INDEX IF NOT EXISTS idx_runs_invoice_number
            ON runs(invoice_number);
        """,
    ),
    (
        3,
        """
        CREATE TABLE review_tasks (
            review_task_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL UNIQUE REFERENCES runs(run_id),
            invoice_number TEXT NOT NULL,
            reason_codes TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """,
    ),
    (
        4,
        """
        ALTER TABLE review_tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'NORMAL';
        ALTER TABLE review_tasks ADD COLUMN updated_at TEXT;
        ALTER TABLE review_tasks ADD COLUMN action TEXT;
        ALTER TABLE review_tasks ADD COLUMN actor TEXT;
        ALTER TABLE review_tasks ADD COLUMN rationale TEXT;
        ALTER TABLE review_tasks ADD COLUMN completed_at TEXT;
        UPDATE review_tasks SET updated_at = created_at WHERE updated_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_review_tasks_status_created
            ON review_tasks(status, created_at);
        """,
    ),
    (
        5,
        """
        ALTER TABLE events ADD COLUMN event_uuid TEXT;
        ALTER TABLE events ADD COLUMN schema_version INTEGER NOT NULL DEFAULT 1;
        ALTER TABLE events ADD COLUMN trace_id TEXT;
        ALTER TABLE events ADD COLUMN span_id TEXT;
        UPDATE events SET event_uuid = 'evt_legacy_' || event_id WHERE event_uuid IS NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_events_event_uuid ON events(event_uuid);
        """,
    ),
)

REVIEW_APPROVAL_BLOCKERS = {
    "DUPLICATE_INVOICE",
    "INSUFFICIENT_STOCK",
    "INVOICE_VERSION_CONFLICT",
    "INVALID_QUANTITY",
    "INVALID_UNIT_PRICE",
    "MISSING_REQUIRED_FIELD",
    "MODEL_OUTPUT_INVALID",
    "MODEL_UNAVAILABLE",
    "REPAIR_EXHAUSTED",
    "SUBTOTAL_MISMATCH",
    "TOTAL_MISMATCH",
    "UNSUPPORTED_CURRENCY",
}


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )"""
            )
            applied = {
                row["version"]
                for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for version, script in MIGRATIONS:
                if version in applied:
                    continue
                connection.executescript(script)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (version, self._now()),
                )
            connection.executemany(
                "INSERT OR IGNORE INTO inventory(item, available_quantity) VALUES (?, ?)",
                [("WidgetA", "15"), ("WidgetB", "10"), ("GadgetX", "5")],
            )

    def create_run(self, run_id: str, source_hash: str, reasoning_mode: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO runs(run_id, source_hash, reasoning_mode, created_at)
                VALUES (?, ?, ?, ?)""",
                (run_id, source_hash, reasoning_mode, self._now()),
            )

    def record_event(self, run_id: str, event_type: str, payload: dict[str, object]) -> None:
        trace_id, span_id = self._trace_context()
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO events(
                    run_id, event_type, payload, created_at,
                    event_uuid, schema_version, trace_id, span_id
                ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                (
                    run_id,
                    event_type,
                    json.dumps(payload, sort_keys=True),
                    self._now(),
                    f"evt_{uuid4().hex}",
                    trace_id,
                    span_id,
                ),
            )

    def complete_run(
        self,
        run_id: str,
        invoice: InvoiceCandidate,
        outcome: Outcome,
        findings: list[Finding],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """UPDATE runs
                SET invoice_number = ?, invoice_fingerprint = ?, outcome = ?
                WHERE run_id = ?""",
                (invoice.invoice_number, self._invoice_fingerprint(invoice), outcome, run_id),
            )
            if outcome is Outcome.ESCALATE:
                now = self._now()
                connection.execute(
                    """INSERT INTO review_tasks(
                        review_task_id, run_id, invoice_number,
                        reason_codes, status, priority, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f"review_{uuid4().hex}",
                        run_id,
                        invoice.invoice_number,
                        json.dumps(sorted({finding.code for finding in findings})),
                        "OPEN",
                        (
                            "HIGH"
                            if any(finding.code == "HIGH_VALUE" for finding in findings)
                            else "NORMAL"
                        ),
                        now,
                        now,
                    ),
                )
        self.record_event(
            run_id,
            "workflow_completed",
            {"outcome": outcome, "finding_codes": [finding.code for finding in findings]},
        )

    def inventory(self) -> dict[str, str]:
        with self._connect() as connection:
            rows = connection.execute("SELECT item, available_quantity FROM inventory").fetchall()
        return {row["item"]: row["available_quantity"] for row in rows}

    def record_payment(
        self, idempotency_key: str, invoice: InvoiceCandidate
    ) -> tuple[str, PaymentStatus, bool]:
        payment_id = f"pay_{uuid4().hex}"
        with self._connect() as connection:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO payments(
                    idempotency_key, payment_id, invoice_number,
                    amount, currency, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    idempotency_key,
                    payment_id,
                    invoice.invoice_number,
                    str(invoice.total_amount),
                    invoice.currency,
                    PaymentStatus.SUCCESS,
                    self._now(),
                ),
            )
            replayed = cursor.rowcount == 0
            row = connection.execute(
                "SELECT payment_id, status FROM payments WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
        if row is None:
            raise RuntimeError("Payment record was not persisted")
        return row["payment_id"], PaymentStatus(row["status"]), replayed

    def payment_count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM payments").fetchone()
        return int(row["count"])

    def review_task_count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM review_tasks").fetchone()
        return int(row["count"])

    def list_review_tasks(self, status: str | None = None) -> list[ReviewTask]:
        query = "SELECT * FROM review_tasks"
        parameters: tuple[str, ...] = ()
        if status:
            query += " WHERE status = ?"
            parameters = (status,)
        query += " ORDER BY CASE priority WHEN 'HIGH' THEN 0 ELSE 1 END, created_at"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._review_task(row) for row in rows]

    def get_review_task(self, review_task_id: str) -> ReviewTask:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM review_tasks WHERE review_task_id = ?", (review_task_id,)
            ).fetchone()
        if row is None:
            raise ValueError(f"Unknown review task {review_task_id}")
        return self._review_task(row)

    def decide_review(
        self,
        review_task_id: str,
        *,
        action: ReviewAction,
        actor: str,
        rationale: str,
    ) -> ReviewTask:
        actor = actor.strip()
        rationale = rationale.strip()
        if not actor or not rationale:
            raise ValueError("Review actor and rationale are required")
        task = self.get_review_task(review_task_id)
        if action not in task.allowed_actions:
            raise ValueError(f"Action {action} is not allowed for {review_task_id}")
        if task.status == "COMPLETED":
            if task.action == action and task.actor == actor and task.rationale == rationale:
                return task
            raise ValueError(f"Review task {review_task_id} is already completed")

        now = self._now()
        trace_id, span_id = self._trace_context()
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE review_tasks
                SET status = 'COMPLETED', action = ?, actor = ?, rationale = ?,
                    completed_at = ?, updated_at = ?
                WHERE review_task_id = ? AND status = 'OPEN'""",
                (action, actor, rationale, now, now, review_task_id),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"Review task {review_task_id} is no longer open")
            connection.execute(
                """INSERT INTO events(
                    run_id, event_type, payload, created_at,
                    event_uuid, schema_version, trace_id, span_id
                ) VALUES (?, 'review_decided', ?, ?, ?, 1, ?, ?)""",
                (
                    task.run_id,
                    json.dumps(
                        {"action": action, "actor": actor, "rationale": rationale},
                        sort_keys=True,
                    ),
                    now,
                    f"evt_{uuid4().hex}",
                    trace_id,
                    span_id,
                ),
            )
        return self.get_review_task(review_task_id)

    def prior_invoice_relation(self, invoice: InvoiceCandidate, source_hash: str) -> str | None:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT source_hash, invoice_fingerprint
                FROM runs
                WHERE invoice_number = ? AND outcome IS NOT NULL
                ORDER BY created_at""",
                (invoice.invoice_number,),
            ).fetchall()
        different_sources = [row for row in rows if row["source_hash"] != source_hash]
        if not different_sources:
            return None
        fingerprint = self._invoice_fingerprint(invoice)
        return (
            "DUPLICATE_INVOICE"
            if any(row["invoice_fingerprint"] == fingerprint for row in different_sources)
            else "INVOICE_VERSION_CONFLICT"
        )

    def schema_version(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations"
            ).fetchone()
        return int(row["version"])

    def event_types(self, run_id: str) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT event_type FROM events WHERE run_id = ? ORDER BY event_id",
                (run_id,),
            ).fetchall()
        return [row["event_type"] for row in rows]

    def events(self, run_id: str) -> list[ReviewEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT event_id, event_uuid, schema_version, event_type,
                    payload, created_at, trace_id, span_id
                FROM events WHERE run_id = ? ORDER BY event_id""",
                (run_id,),
            ).fetchall()
        return self._events(rows)

    def events_after(self, sequence: int = 0) -> list[ReviewEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT event_id, event_uuid, schema_version, event_type,
                    payload, created_at, trace_id, span_id
                FROM events WHERE event_id > ? ORDER BY event_id""",
                (sequence,),
            ).fetchall()
        return self._events(rows)

    @staticmethod
    def _events(rows: list[sqlite3.Row]) -> list[ReviewEvent]:
        return [
            ReviewEvent(
                sequence=row["event_id"],
                event_id=row["event_uuid"],
                schema_version=row["schema_version"],
                event_type=row["event_type"],
                payload=json.loads(row["payload"]),
                created_at=row["created_at"],
                trace_id=row["trace_id"],
                span_id=row["span_id"],
            )
            for row in rows
        ]

    @staticmethod
    def _review_task(row: sqlite3.Row) -> ReviewTask:
        reason_codes = json.loads(row["reason_codes"])
        allowed_actions = [ReviewAction.REJECT, ReviewAction.REQUEST_CORRECTION]
        if not REVIEW_APPROVAL_BLOCKERS.intersection(reason_codes):
            allowed_actions.insert(0, ReviewAction.APPROVE)
        return ReviewTask(
            review_task_id=row["review_task_id"],
            run_id=row["run_id"],
            invoice_number=row["invoice_number"],
            reason_codes=reason_codes,
            status=row["status"],
            priority=row["priority"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            allowed_actions=allowed_actions,
            action=row["action"],
            actor=row["actor"],
            rationale=row["rationale"],
            completed_at=row["completed_at"],
        )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _trace_context() -> tuple[str | None, str | None]:
        context = trace.get_current_span().get_span_context()
        if not context.is_valid:
            return None, None
        return f"{context.trace_id:032x}", f"{context.span_id:016x}"

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _invoice_fingerprint(invoice: InvoiceCandidate) -> str:
        payment_facts = {
            "currency": invoice.currency,
            "invoice_number": invoice.invoice_number,
            "line_items": sorted(
                (
                    line.item.casefold(),
                    SQLiteStore._canonical_decimal(line.quantity),
                    SQLiteStore._canonical_decimal(line.unit_price),
                )
                for line in invoice.line_items
            ),
            "shipping": SQLiteStore._canonical_decimal(invoice.shipping),
            "subtotal": SQLiteStore._canonical_decimal(invoice.subtotal),
            "tax": SQLiteStore._canonical_decimal(invoice.tax),
            "total_amount": SQLiteStore._canonical_decimal(invoice.total_amount),
        }
        return sha256(json.dumps(payment_facts, sort_keys=True).encode()).hexdigest()

    @staticmethod
    def _canonical_decimal(value: Decimal) -> str:
        return format(value.normalize(), "f")
