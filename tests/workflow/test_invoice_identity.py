from pathlib import Path

import pytest

from intellipay.config import Settings
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.models import Outcome, PaymentStatus
from intellipay.workflow.storage import SQLiteStore


def test_revised_invoice_conflict_cannot_create_second_payment(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    workflow = InvoiceWorkflow(Settings(database_path=database, _env_file=None))

    original = workflow.process(Path("data/invoices/invoice_1004.json"))
    revision = workflow.process(Path("data/invoices/invoice_1004_revised.json"))

    assert original.outcome is Outcome.APPROVE
    assert original.payment_status is PaymentStatus.SUCCESS
    assert revision.outcome is Outcome.ESCALATE
    assert "INVOICE_VERSION_CONFLICT" in {finding.code for finding in revision.findings}
    assert revision.payment_status is PaymentStatus.NOT_ATTEMPTED
    assert SQLiteStore(database).payment_count() == 1
    assert SQLiteStore(database).review_task_count() == 1


@pytest.mark.parametrize("invoice_number", ["1011", "1012"])
def test_equivalent_txt_and_pdf_are_duplicate_without_second_payment(
    tmp_path: Path, invoice_number: str
) -> None:
    database = tmp_path / "intellipay.db"
    workflow = InvoiceWorkflow(Settings(database_path=database, _env_file=None))

    text = workflow.process(Path(f"data/invoices/invoice_{invoice_number}.txt"))
    pdf = workflow.process(Path(f"data/invoices/invoice_{invoice_number}.pdf"))

    assert text.outcome is Outcome.APPROVE
    assert pdf.outcome is Outcome.ESCALATE
    assert "DUPLICATE_INVOICE" in {finding.code for finding in pdf.findings}
    assert pdf.payment_status is PaymentStatus.NOT_ATTEMPTED
    assert SQLiteStore(database).payment_count() == 1
    assert SQLiteStore(database).review_task_count() == 1


def test_decimal_formatting_does_not_create_false_version_conflict(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    workflow = InvoiceWorkflow(Settings(database_path=database, _env_file=None))

    workflow.process(Path("data/invoices/invoice_1013.json"))
    pdf = workflow.process(Path("data/invoices/invoice_1013.pdf"))

    finding_codes = {finding.code for finding in pdf.findings}
    assert "DUPLICATE_INVOICE" in finding_codes
    assert "INVOICE_VERSION_CONFLICT" not in finding_codes
    assert SQLiteStore(database).payment_count() == 0
