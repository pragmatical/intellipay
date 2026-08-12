from pathlib import Path

from intellipay.config import Settings
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.models import Outcome, PaymentStatus
from intellipay.workflow.storage import SQLiteStore

INVOICE = Path("data/invoices/invoice_1001.txt")


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
