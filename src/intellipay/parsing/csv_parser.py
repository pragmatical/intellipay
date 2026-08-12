import csv
import io

from intellipay.parsing.common import decimal_value, normalize_date
from intellipay.reasoning.models import Currency, InvoiceCandidate, LineItem


def parse_csv_invoice(content: bytes) -> InvoiceCandidate:
    text = content.decode("utf-8-sig")
    first_row = next(csv.reader(io.StringIO(text)))
    if first_row == ["field", "value"]:
        return _parse_key_value(text)
    return _parse_tabular(text)


def _parse_key_value(text: str) -> InvoiceCandidate:
    rows = list(csv.DictReader(io.StringIO(text)))
    values: dict[str, str] = {}
    line_items: list[LineItem] = []
    current: dict[str, str] = {}
    for row in rows:
        field = row["field"].strip()
        value = row["value"].strip()
        if field == "item" and current:
            line_items.append(_line_item(current))
            current = {}
        if field in {"item", "quantity", "unit_price"}:
            current[field] = value
        else:
            values[field] = value
    if current:
        line_items.append(_line_item(current))
    return InvoiceCandidate(
        vendor_name=values.get("vendor", ""),
        invoice_number=values.get("invoice_number", ""),
        invoice_date=normalize_date(values.get("date")),
        due_date=normalize_date(values.get("due_date")) or None,
        currency=Currency.USD,
        subtotal=decimal_value(values.get("subtotal")),
        tax=decimal_value(values.get("tax")),
        total_amount=decimal_value(values.get("total")),
        payment_terms=values.get("payment_terms", "Not stated"),
        line_items=line_items,
    )


def _parse_tabular(text: str) -> InvoiceCandidate:
    rows = list(csv.DictReader(io.StringIO(text)))
    item_rows = [row for row in rows if row.get("Item")]
    first = item_rows[0] if item_rows else {}
    totals = {
        row.get("Unit Price", "").rstrip(":").split(" (")[0].lower(): row.get("Line Total", "")
        for row in rows
        if not row.get("Item") and row.get("Unit Price")
    }
    return InvoiceCandidate(
        vendor_name=first.get("Vendor", ""),
        invoice_number=first.get("Invoice Number", ""),
        invoice_date=normalize_date(first.get("Date")),
        due_date=normalize_date(first.get("Due Date")) or None,
        currency=Currency.USD,
        subtotal=decimal_value(totals.get("subtotal")),
        tax=decimal_value(totals.get("tax")),
        total_amount=decimal_value(totals.get("total")),
        payment_terms="Not stated",
        line_items=[
            LineItem(
                item=row["Item"].strip(),
                quantity=decimal_value(row["Qty"]),
                unit_price=decimal_value(row["Unit Price"]),
            )
            for row in item_rows
        ],
    )


def _line_item(values: dict[str, str]) -> LineItem:
    return LineItem(
        item=values.get("item", ""),
        quantity=decimal_value(values.get("quantity")),
        unit_price=decimal_value(values.get("unit_price")),
    )
