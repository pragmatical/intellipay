from pathlib import Path

import pytest

from intellipay.config import Settings
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.models import Outcome, PaymentStatus, ReviewAction
from intellipay.workflow.storage import SQLiteStore


def test_review_decision_is_durable_and_idempotent(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    workflow = InvoiceWorkflow(Settings(database_path=database, _env_file=None))
    result = workflow.process(Path("data/invoices/invoice_1002.txt"))
    store = SQLiteStore(database)
    task = store.list_review_tasks()[0]

    decision = store.decide_review(
        task.review_task_id,
        action=ReviewAction.REJECT,
        actor="ap.reviewer@example.com",
        rationale="Inventory evidence does not support payment.",
    )
    replay = store.decide_review(
        task.review_task_id,
        action=ReviewAction.REJECT,
        actor="ap.reviewer@example.com",
        rationale="Inventory evidence does not support payment.",
    )

    assert task.run_id == result.run_id
    assert task.allowed_actions == [ReviewAction.REJECT, ReviewAction.REQUEST_CORRECTION]
    assert decision == replay
    assert decision.status == "COMPLETED"
    assert decision.actor == "ap.reviewer@example.com"
    assert store.event_types(result.run_id).count("review_decided") == 1


def test_disallowed_review_approval_is_rejected(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    workflow = InvoiceWorkflow(Settings(database_path=database, _env_file=None))
    workflow.process(Path("data/invoices/invoice_1014.xml"))
    store = SQLiteStore(database)
    task = store.list_review_tasks()[0]

    with pytest.raises(ValueError, match="not allowed"):
        store.decide_review(
            task.review_task_id,
            action=ReviewAction.APPROVE,
            actor="ap.reviewer@example.com",
            rationale="Pay it anyway.",
        )


def test_approved_soft_exception_resumes_same_run_once(tmp_path: Path) -> None:
    source = tmp_path / "high-value.json"
    source.write_text(
        """{
            "vendor": {"name": "Acme Supplies"},
            "invoice_number": "INV-REVIEW-1",
            "date": "2026-08-01",
            "due_date": "2026-08-31",
            "currency": "USD",
            "subtotal": 12000,
            "tax": 0,
            "total": 12000,
            "payment_terms": "Net 30",
            "line_items": [
                {"item": "WidgetA", "quantity": 1, "unit_price": 12000}
            ]
        }"""
    )
    database = tmp_path / "intellipay.db"
    workflow = InvoiceWorkflow(Settings(database_path=database, _env_file=None))
    escalated = workflow.process(source)
    store = SQLiteStore(database)
    task = store.list_review_tasks()[0]

    completed = workflow.resolve_review(
        task.review_task_id,
        action=ReviewAction.APPROVE,
        actor="ap.reviewer@example.com",
        rationale="Verified source and delegated high-value approval.",
    )
    replay = workflow.resolve_review(
        task.review_task_id,
        action=ReviewAction.APPROVE,
        actor="ap.reviewer@example.com",
        rationale="Verified source and delegated high-value approval.",
    )

    assert escalated.outcome is Outcome.ESCALATE
    assert completed.run_id == escalated.run_id == replay.run_id
    assert completed.outcome is Outcome.APPROVE
    assert completed.payment_status is PaymentStatus.SUCCESS
    assert completed.payment_id == replay.payment_id
    assert store.payment_count() == 1
    assert store.event_types(completed.run_id).count("review_decided") == 1
