from pathlib import Path

from intellipay.config import Settings
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.models import Outcome, PaymentStatus
from intellipay.workflow.storage import SQLiteStore

INVOICE = Path("data/invoices/invoice_1001.txt")


def test_migrations_are_repeatable(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "intellipay.db")

    store.initialize()
    first_inventory = store.inventory()
    store.initialize()

    assert store.schema_version() == 5
    assert (
        store.inventory()
        == first_inventory
        == {
            "GadgetX": "5",
            "WidgetA": "15",
            "WidgetB": "10",
        }
    )


def test_inv_1001_pays_once_after_duplicate_submission(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    settings = Settings(database_path=database, _env_file=None)
    workflow = InvoiceWorkflow(settings)

    first = workflow.process(INVOICE)
    second = workflow.process(INVOICE)

    assert first.outcome is Outcome.APPROVE
    assert first.findings == []
    assert first.payment_status is PaymentStatus.SUCCESS
    assert first.payment_replayed is False
    assert second.outcome is Outcome.APPROVE
    assert second.payment_status is PaymentStatus.SUCCESS
    assert second.payment_id == first.payment_id
    assert second.payment_replayed is True
    assert SQLiteStore(database).payment_count() == 1


def test_completed_run_resumes_from_checkpoint_without_repeating_payment(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    settings = Settings(database_path=database, _env_file=None)
    first_workflow = InvoiceWorkflow(settings)
    completed = first_workflow.process(INVOICE)
    events_before_resume = completed.event_types

    resumed = InvoiceWorkflow(settings).resume(completed.run_id)

    assert resumed.payment_id == completed.payment_id
    assert resumed.payment_status is PaymentStatus.SUCCESS
    assert resumed.event_types == events_before_resume
    assert SQLiteStore(database).payment_count() == 1


def test_payment_requires_authorization_and_records_evidence(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    result = InvoiceWorkflow(Settings(database_path=database, _env_file=None)).process(INVOICE)

    assert result.payment_authorized is True
    assert result.inventory_snapshot == {"GadgetX": "5", "WidgetA": "15", "WidgetB": "10"}
    assert result.policy_rules_fired == ["NO_HARD_FINDINGS", "PAYMENT_AUTHORIZED"]
    assert result.event_types.index("invoice_validated") < result.event_types.index(
        "invoice_decided"
    )
    assert result.event_types.index("invoice_decided") < result.event_types.index(
        "payment_authorized"
    )
    assert result.event_types.index("payment_authorized") < result.event_types.index(
        "payment_recorded"
    )


def test_negative_quantity_rejects_without_payment(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    invalid_invoice = tmp_path / "invoice_negative.txt"
    invalid_invoice.write_text(INVOICE.read_text().replace("qty: 10", "qty: -10"))
    settings = Settings(database_path=database, _env_file=None)

    result = InvoiceWorkflow(settings).process(invalid_invoice)

    assert result.outcome is Outcome.REJECT
    assert {finding.code for finding in result.findings} >= {
        "INVALID_QUANTITY",
        "SUBTOTAL_MISMATCH",
    }
    assert result.payment_status is PaymentStatus.NOT_ATTEMPTED
    assert result.payment_id is None
    assert SQLiteStore(database).payment_count() == 0


def test_ambiguous_subtotal_completes_one_bounded_repair(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    ambiguous_invoice = tmp_path / "invoice_ambiguous.txt"
    ambiguous_invoice.write_text(INVOICE.read_text().replace("$5,000.00", "$5,OOO.OO", 1))
    settings = Settings(database_path=database, _env_file=None)

    result = InvoiceWorkflow(settings).process(ambiguous_invoice)

    assert result.outcome is Outcome.APPROVE
    assert result.findings == []
    assert result.repair_attempts == 1
    assert [defect.code for defect in result.extraction_defects] == [
        "SUBTOTAL_INCONSISTENT_WITH_LINES"
    ]
    assert result.invoice.subtotal == 5000
    assert result.payment_status is PaymentStatus.SUCCESS


def test_json_invoice_uses_deterministic_parser(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    settings = Settings(database_path=database, _env_file=None)

    result = InvoiceWorkflow(settings).process(Path("data/invoices/invoice_1004.json"))

    assert result.invoice.invoice_number == "INV-1004"
    assert result.invoice.total_amount == 1890
    assert result.event_types[0] == "invoice_extracted"


def test_malformed_json_preserves_missing_values_for_findings(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    settings = Settings(database_path=database, _env_file=None)

    result = InvoiceWorkflow(settings).process(Path("data/invoices/invoice_1009.json"))

    assert result.outcome is Outcome.REJECT
    assert "MISSING_REQUIRED_FIELD" in {finding.code for finding in result.findings}
    assert result.payment_status is PaymentStatus.NOT_ATTEMPTED
