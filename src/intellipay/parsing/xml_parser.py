from xml.etree import ElementTree

from intellipay.parsing.common import decimal_value, normalize_date
from intellipay.reasoning.models import Currency, InvoiceCandidate, LineItem


def parse_xml_invoice(content: bytes) -> InvoiceCandidate:
    root = ElementTree.fromstring(content)
    return InvoiceCandidate(
        vendor_name=_text(root, "./header/vendor"),
        invoice_number=_text(root, "./header/invoice_number"),
        invoice_date=normalize_date(_text(root, "./header/date")),
        due_date=normalize_date(_text(root, "./header/due_date")) or None,
        currency=Currency(_text(root, "./header/currency") or "USD"),
        subtotal=decimal_value(_text(root, "./totals/subtotal")),
        tax=decimal_value(_text(root, "./totals/tax_amount")),
        total_amount=decimal_value(_text(root, "./totals/total")),
        payment_terms=_text(root, "./payment_terms"),
        line_items=[
            LineItem(
                item=_text(item, "./name"),
                quantity=decimal_value(_text(item, "./quantity")),
                unit_price=decimal_value(_text(item, "./unit_price")),
            )
            for item in root.findall("./line_items/item")
        ],
    )


def _text(element: ElementTree.Element, path: str) -> str:
    value = element.findtext(path)
    return value.strip() if value else ""
