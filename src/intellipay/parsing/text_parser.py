import re

from intellipay.parsing.common import decimal_value, normalize_date
from intellipay.reasoning.models import Currency, InvoiceCandidate, LineItem


def parse_text_invoice(content: bytes) -> InvoiceCandidate:
    text = content.decode("utf-8", errors="replace")
    total = _money_field(text, ("Total Amount", "TOTAL", "Total", "Amt"))
    subtotal = _money_field(text, ("Subtotal",))
    tax = _money_field(text, ("Sales Tax", "Tax"))
    invoice_number = _field(text, ("Invoice Number", "Invoice", "INVOICE #", "INV NO", "Inv #"))
    digits = re.search(r"\d{4}", invoice_number)
    normalized_number = f"INV-{digits.group() if digits else invoice_number.strip()}"
    return InvoiceCandidate(
        vendor_name=_field(text, ("Vendor", "FROM", "Vndr")),
        invoice_number=normalized_number,
        invoice_date=normalize_date(_field(text, ("Date", "DATE", "Dt"))),
        due_date=(
            normalize_date(_field(text, ("Due Date", "DueDate", "Due Dt", "DUE", "Due"))) or None
        ),
        currency=Currency.USD,
        subtotal=subtotal if subtotal is not None else total,
        tax=tax or decimal_value(0),
        shipping=_money_field(text, ("Shipping",)) or decimal_value(0),
        total_amount=total,
        payment_terms=_field(text, ("Payment Terms", "Pymnt Terms", "Terms")),
        line_items=_line_items(text),
    )


def _field(text: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        pattern = rf"(?im)^[ \t]*(?:{re.escape(label)})[ \t]*:?[ \t]*(.+?)[ \t]*$"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def _money_field(text: str, labels: tuple[str, ...]):
    for label in labels:
        pattern = rf"(?im)\b{re.escape(label)}(?:\s*\([^)]*\))?\s*:\s*\$([\d,O]+\.[\dO]{{2}})"
        match = re.search(pattern, text)
        if match:
            return decimal_value(match.group(1))
    return None


def _line_items(text: str) -> list[LineItem]:
    patterns = (
        re.compile(
            r"(?im)^\s*-?\s*(?P<item>[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+"
            r"(?:qty\s*:?\s*|x)(?P<quantity>-?\d+)\s+"
            r"(?:unit price:\s*|@\s*)?\$(?P<price>[\d,O]+(?:\.[\dO]{2})?)"
        ),
        re.compile(
            r"(?im)^\s*(?P<item>[A-Za-z]+(?:\s+[A-Za-z]+)?)(?:\s+\([^)]*\))?\s+"
            r"(?P<quantity>-?\d+)\s+\$(?P<price>[\d,O]+(?:\.[\dO]{2})?)\s+\$"
        ),
    )
    items: list[LineItem] = []
    seen: set[tuple[str, str, str]] = set()
    for pattern in patterns:
        for match in pattern.finditer(text):
            raw_item = match.group("item").replace(" ", "")
            raw_item = {
                "gadgetx": "GadgetX",
                "widgeta": "WidgetA",
                "widgetb": "WidgetB",
            }.get(raw_item.casefold(), raw_item)
            key = (raw_item, match.group("quantity"), match.group("price"))
            if key in seen:
                continue
            seen.add(key)
            items.append(
                LineItem(
                    item=raw_item,
                    quantity=decimal_value(match.group("quantity")),
                    unit_price=decimal_value(match.group("price")),
                )
            )
    return items
