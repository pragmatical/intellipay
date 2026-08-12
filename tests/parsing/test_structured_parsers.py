from pathlib import Path

from intellipay.parsing import ParserRegistry
from intellipay.reasoning.models import Currency


def parse(path: str):
    source = Path(path)
    return ParserRegistry().parse(source, source.read_bytes())


def test_key_value_csv() -> None:
    invoice = parse("data/invoices/invoice_1006.csv")

    assert invoice.invoice_number == "INV-1006"
    assert invoice.total_amount == 2750
    assert len(invoice.line_items) == 2


def test_tabular_csv_preserves_arithmetic_discrepancy() -> None:
    invoice = parse("data/invoices/invoice_1007.csv")

    assert invoice.invoice_date == "2026-01-28"
    assert invoice.subtotal == 14750
    assert invoice.tax == 885
    assert invoice.total_amount == 15525


def test_xml_preserves_eur() -> None:
    invoice = parse("data/invoices/invoice_1014.xml")

    assert invoice.currency is Currency.EUR
    assert invoice.total_amount == 4125
    assert len(invoice.line_items) == 2
