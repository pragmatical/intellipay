from pathlib import Path

import pytest

from intellipay.parsing import ParserRegistry


@pytest.mark.parametrize(
    ("filename", "invoice_number", "line_count", "total"),
    [
        ("invoice_1001.txt", "INV-1001", 2, 5000),
        ("invoice_1002.txt", "INV-1002", 1, 15000),
        ("invoice_1003.txt", "INV-1003", 1, 100000),
        ("invoice_1008.txt", "INV-1008", 2, 9900),
        ("invoice_1010.txt", "INV-1010", 4, 7185),
        ("invoice_1011.txt", "INV-1011", 2, 3000),
        ("invoice_1012.txt", "INV-1012", 3, 9975),
    ],
)
def test_txt_variants(filename: str, invoice_number: str, line_count: int, total: int) -> None:
    path = Path("data/invoices") / filename
    invoice = ParserRegistry().parse(path, path.read_bytes())

    assert invoice.invoice_number == invoice_number
    assert len(invoice.line_items) == line_count
    assert invoice.total_amount == total
