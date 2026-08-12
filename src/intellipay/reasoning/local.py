import re
from decimal import Decimal
from typing import ClassVar

from intellipay.config import ReasoningMode
from intellipay.reasoning.models import (
    Currency,
    DecisionCritique,
    DecisionCritiqueRequest,
    DecisionCritiqueResult,
    ExtractionCritique,
    ExtractionCritiqueRequest,
    ExtractionDefect,
    ExtractionRepairRequest,
    ExtractionRequest,
    ExtractionResult,
    InvoiceCandidate,
    LineItem,
)


class LocalReasoningProvider:
    """Deterministic simulation of the external reasoning contract."""

    _FIELD_PATTERNS: ClassVar[dict[str, str]] = {
        "vendor_name": r"^Vendor:\s*(.+)$",
        "invoice_number": r"^Invoice Number:\s*(.+)$",
        "invoice_date": r"^Date:\s*(.+)$",
        "due_date": r"^Due Date:\s*(.+)$",
        "subtotal": r"^Subtotal:\s*\$([\dO,]+\.[\dO]{2})$",
        "tax": r"^Tax.*:\s*\$([\d,]+\.\d{2})$",
        "total_amount": r"^Total Amount:\s*\$([\d,]+\.\d{2})$",
        "payment_terms": r"^Payment Terms:\s*(.+)$",
    }
    _ITEM_PATTERN = re.compile(
        r"^\s*(?P<item>\w+)\s+qty:\s*(?P<quantity>-?[\d.]+)\s+"
        r"unit price:\s*\$(?P<unit_price>[\d,]+\.\d{2})$",
        re.MULTILINE,
    )

    def extract_invoice(self, request: ExtractionRequest) -> ExtractionResult:
        fields = {
            name: self._required_match(pattern, request.content)
            for name, pattern in self._FIELD_PATTERNS.items()
        }
        line_items = [
            LineItem(
                item=match.group("item"),
                quantity=Decimal(match.group("quantity")),
                unit_price=self._money(match.group("unit_price")),
            )
            for match in self._ITEM_PATTERN.finditer(request.content)
        ]
        candidate = InvoiceCandidate(
            vendor_name=fields["vendor_name"],
            invoice_number=fields["invoice_number"],
            invoice_date=fields["invoice_date"],
            due_date=fields["due_date"],
            currency=Currency.USD,
            subtotal=self._money(fields["subtotal"], preserve_ocr_error=True),
            tax=self._money(fields["tax"]),
            total_amount=self._money(fields["total_amount"]),
            payment_terms=fields["payment_terms"],
            line_items=line_items,
        )
        return ExtractionResult(
            mode=ReasoningMode.LOCAL,
            provider="simulated",
            model="deterministic-v1",
            candidate=candidate,
        )

    def critique_extraction(self, request: ExtractionCritiqueRequest) -> ExtractionCritique:
        defects = []
        if "SUBTOTAL_MISMATCH" in request.finding_codes:
            defects.append(
                ExtractionDefect(
                    code="SUBTOTAL_INCONSISTENT_WITH_LINES",
                    field="subtotal",
                    message="Subtotal does not equal the sum of line items.",
                )
            )
        return ExtractionCritique(defects=defects)

    def repair_invoice(self, request: ExtractionRepairRequest) -> ExtractionResult:
        result = self.extract_invoice(request.extraction)
        subtotal_match = self._required_match(
            self._FIELD_PATTERNS["subtotal"], request.extraction.content
        )
        return result.model_copy(
            update={
                "candidate": result.candidate.model_copy(
                    update={"subtotal": self._money(subtotal_match)}
                )
            }
        )

    def critique_decision(self, request: DecisionCritiqueRequest) -> DecisionCritiqueResult:
        defects = (
            ["Findings are present; automated approval must not become less strict."]
            if request.findings and request.proposed_outcome == "APPROVE"
            else []
        )
        return DecisionCritiqueResult(
            mode=ReasoningMode.LOCAL,
            provider="simulated",
            model="deterministic-v1",
            critique=DecisionCritique(accept_recommendation=not defects, defects=defects),
        )

    @staticmethod
    def _required_match(pattern: str, content: str) -> str:
        match = re.search(pattern, content, re.MULTILINE)
        if match is None:
            raise ValueError(f"Local simulation could not match required pattern: {pattern}")
        return match.group(1).strip()

    @staticmethod
    def _money(value: str, *, preserve_ocr_error: bool = False) -> Decimal:
        if preserve_ocr_error and "O" in value:
            return Decimal("500.00")
        return Decimal(value.replace(",", "").replace("O", "0"))
