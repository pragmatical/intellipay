from pathlib import Path

import pytest

from intellipay.config import Settings
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.models import Outcome, PaymentStatus
from intellipay.workflow.storage import SQLiteStore


@pytest.mark.parametrize(
    ("filename", "expected_outcome", "expected_findings"),
    [
        (
            "invoice_1002.txt",
            Outcome.ESCALATE,
            {"HIGH_VALUE", "INSUFFICIENT_STOCK", "PAYMENT_TERMS_DATE_MISMATCH"},
        ),
        (
            "invoice_1003.txt",
            Outcome.ESCALATE,
            {"HIGH_VALUE", "INVALID_DATE", "UNKNOWN_ITEM"},
        ),
        (
            "invoice_1007.csv",
            Outcome.REJECT,
            {"HIGH_VALUE", "INSUFFICIENT_STOCK", "TOTAL_MISMATCH"},
        ),
        (
            "invoice_1008.txt",
            Outcome.ESCALATE,
            {"NEAR_THRESHOLD_RISK", "UNKNOWN_ITEM"},
        ),
        (
            "invoice_1009.json",
            Outcome.REJECT,
            {"MISSING_REQUIRED_FIELD"},
        ),
        (
            "invoice_1013.json",
            Outcome.REJECT,
            {"HIGH_VALUE", "INSUFFICIENT_STOCK", "TOTAL_MISMATCH"},
        ),
        (
            "invoice_1014.xml",
            Outcome.ESCALATE,
            {"UNSUPPORTED_CURRENCY"},
        ),
    ],
)
def test_stage_two_controls_block_payment(
    tmp_path: Path,
    filename: str,
    expected_outcome: Outcome,
    expected_findings: set[str],
) -> None:
    database = tmp_path / "intellipay.db"
    workflow = InvoiceWorkflow(Settings(database_path=database, _env_file=None))

    result = workflow.process(Path("data/invoices") / filename)

    assert result.outcome is expected_outcome
    assert {finding.code for finding in result.findings} >= expected_findings
    assert result.payment_authorized is False
    assert result.payment_status is PaymentStatus.NOT_ATTEMPTED
    assert result.payment_id is None
    assert SQLiteStore(database).payment_count() == 0


def test_inv_1013_aggregates_repeated_item_quantities(tmp_path: Path) -> None:
    result = InvoiceWorkflow(
        Settings(database_path=tmp_path / "intellipay.db", _env_file=None)
    ).process(Path("data/invoices/invoice_1013.json"))

    stock_findings = [
        finding.message for finding in result.findings if finding.code == "INSUFFICIENT_STOCK"
    ]
    assert stock_findings == [
        "WidgetA requests 22; 15 available",
        "WidgetB requests 18; 10 available",
        "GadgetX requests 9; 5 available",
    ]
