from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from intellipay.config import ReasoningMode


class Currency(StrEnum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class LineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: str = Field(min_length=1)
    quantity: Decimal
    unit_price: Decimal


class InvoiceCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vendor_name: str
    invoice_number: str
    invoice_date: str
    due_date: str | None
    currency: Currency
    subtotal: Decimal
    tax: Decimal
    shipping: Decimal = Decimal()
    total_amount: Decimal
    payment_terms: str
    line_items: list[LineItem]


class ExtractionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=1)
    content: str = Field(min_length=1)


class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: ReasoningMode
    provider: str
    model: str
    candidate: InvoiceCandidate


class ExtractionDefect(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    field: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ExtractionCritiqueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate: InvoiceCandidate
    finding_codes: list[str]


class ExtractionCritique(BaseModel):
    model_config = ConfigDict(extra="forbid")

    defects: list[ExtractionDefect]


class ExtractionRepairRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction: ExtractionRequest
    candidate: InvoiceCandidate
    defects: list[ExtractionDefect]
    attempt: int = Field(ge=1)


class DecisionCritiqueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_number: str = Field(min_length=1)
    proposed_outcome: str = Field(min_length=1)
    findings: list[str]


class DecisionCritique(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accept_recommendation: bool
    defects: list[str]


class DecisionCritiqueResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: ReasoningMode
    provider: str
    model: str
    critique: DecisionCritique
