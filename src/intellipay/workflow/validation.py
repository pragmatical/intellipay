from collections import defaultdict
from decimal import Decimal

from intellipay.reasoning.models import InvoiceCandidate
from intellipay.workflow.models import Finding


def validate_invoice(invoice: InvoiceCandidate, inventory: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    requested: defaultdict[str, Decimal] = defaultdict(Decimal)

    for line in invoice.line_items:
        if line.quantity <= 0:
            findings.append(
                Finding(code="INVALID_QUANTITY", message=f"{line.item} quantity must be positive")
            )
        if line.unit_price < 0:
            findings.append(
                Finding(
                    code="INVALID_UNIT_PRICE",
                    message=f"{line.item} price must not be negative",
                )
            )
        requested[line.item] += line.quantity

    for item, quantity in requested.items():
        available = inventory.get(item)
        if available is None:
            findings.append(Finding(code="UNKNOWN_ITEM", message=f"{item} is not in inventory"))
        elif quantity > Decimal(available):
            findings.append(
                Finding(
                    code="INSUFFICIENT_STOCK",
                    message=f"{item} requests {quantity}; {available} available",
                )
            )

    calculated_subtotal = sum(
        (line.quantity * line.unit_price for line in invoice.line_items), start=Decimal()
    )
    if calculated_subtotal != invoice.subtotal:
        findings.append(
            Finding(
                code="SUBTOTAL_MISMATCH",
                message=f"Calculated {calculated_subtotal}; stated {invoice.subtotal}",
            )
        )
    calculated_total = invoice.subtotal + invoice.tax
    if calculated_total != invoice.total_amount:
        findings.append(
            Finding(
                code="TOTAL_MISMATCH",
                message=f"Calculated {calculated_total}; stated {invoice.total_amount}",
            )
        )
    return findings
