import json
from decimal import Decimal

from intellipay.reasoning.models import Currency, InvoiceCandidate, LineItem


def parse_json_invoice(content: bytes) -> InvoiceCandidate:
    data = json.loads(content)
    vendor = data.get("vendor") or {}
    line_items = [
        LineItem(
            item=str(line.get("item") or ""),
            quantity=Decimal(str(line.get("quantity") or 0)),
            unit_price=Decimal(str(line.get("unit_price") or 0)),
        )
        for line in data.get("line_items") or []
    ]
    return InvoiceCandidate(
        vendor_name=str(vendor.get("name") or ""),
        invoice_number=str(data.get("invoice_number") or ""),
        invoice_date=str(data.get("date") or data.get("invoice_date") or ""),
        due_date=data.get("due_date"),
        currency=Currency(data.get("currency") or "USD"),
        subtotal=Decimal(str(data.get("subtotal") or 0)),
        tax=Decimal(str(data.get("tax_amount") or data.get("tax") or 0)),
        shipping=Decimal(str(data.get("shipping") or 0)),
        total_amount=Decimal(str(data.get("total") or data.get("total_amount") or 0)),
        payment_terms=str(data.get("payment_terms") or ""),
        line_items=line_items,
    )
