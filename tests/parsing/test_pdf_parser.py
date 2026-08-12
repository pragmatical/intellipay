from decimal import Decimal
from pathlib import Path

import pytest

from intellipay.parsing import ParserRegistry


@pytest.mark.parametrize(
    ("filename", "invoice_number", "line_count", "total"),
    [
        ("invoice_1011.pdf", "INV-1011", 2, Decimal("3000")),
        ("invoice_1012.pdf", "INV-1012", 3, Decimal("9975")),
        ("invoice_1013.pdf", "INV-1013", 8, Decimal("22562.80")),
    ],
)
def test_image_pdf_variants(
    filename: str, invoice_number: str, line_count: int, total: Decimal
) -> None:
    path = Path("data/invoices") / filename
    invoice = ParserRegistry().parse(path, path.read_bytes())

    assert invoice.invoice_number == invoice_number
    assert len(invoice.line_items) == line_count
    assert invoice.total_amount == total
