import re
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from intellipay.reasoning.models import Currency, InvoiceCandidate
from intellipay.workflow.models import Finding

ENHANCED_REVIEW_THRESHOLD = Decimal("10000")
NEAR_THRESHOLD_LOWER_BOUND = Decimal("9500")


def validate_invoice(invoice: InvoiceCandidate, inventory: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    requested: defaultdict[str, Decimal] = defaultdict(Decimal)

    required_values = {
        "vendor_name": invoice.vendor_name,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "due_date": invoice.due_date,
    }
    for field, value in required_values.items():
        if value is None or not str(value).strip():
            findings.append(Finding(code="MISSING_REQUIRED_FIELD", message=f"{field} is required"))
    if not invoice.line_items:
        findings.append(Finding(code="MISSING_REQUIRED_FIELD", message="line_items are required"))

    invoice_date = _parse_date(invoice.invoice_date, "invoice_date", findings)
    due_date = _parse_date(invoice.due_date, "due_date", findings)
    term_match = re.fullmatch(r"Net\s+(\d+)", invoice.payment_terms, flags=re.IGNORECASE)
    if invoice_date and due_date and term_match:
        earliest_due_date = invoice_date + timedelta(days=int(term_match.group(1)))
        if due_date + timedelta(days=2) < earliest_due_date:
            findings.append(
                Finding(
                    code="PAYMENT_TERMS_DATE_MISMATCH",
                    message=(
                        f"Due date {due_date.isoformat()} is earlier than "
                        f"{invoice.payment_terms} from {invoice_date.isoformat()}"
                    ),
                )
            )

    if invoice.currency is not Currency.USD:
        findings.append(
            Finding(
                code="UNSUPPORTED_CURRENCY",
                message=f"No payment policy is configured for {invoice.currency}",
            )
        )

    if invoice.total_amount >= ENHANCED_REVIEW_THRESHOLD:
        findings.append(
            Finding(
                code="HIGH_VALUE",
                message=f"Total {invoice.total_amount} requires enhanced review",
            )
        )

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

    has_unknown_item = any(finding.code == "UNKNOWN_ITEM" for finding in findings)
    if (
        NEAR_THRESHOLD_LOWER_BOUND <= invoice.total_amount < ENHANCED_REVIEW_THRESHOLD
        and has_unknown_item
    ):
        findings.append(
            Finding(
                code="NEAR_THRESHOLD_RISK",
                message=(
                    f"Total {invoice.total_amount} is near the enhanced-review threshold "
                    "and includes unknown items"
                ),
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
    calculated_total = invoice.subtotal + invoice.tax + invoice.shipping
    if calculated_total != invoice.total_amount:
        findings.append(
            Finding(
                code="TOTAL_MISMATCH",
                message=f"Calculated {calculated_total}; stated {invoice.total_amount}",
            )
        )
    return findings


def _parse_date(value: str | None, field: str, findings: list[Finding]) -> date | None:
    if value is None or not value.strip():
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        findings.append(
            Finding(code="INVALID_DATE", message=f"{field} is not a valid ISO date: {value}")
        )
        return None
