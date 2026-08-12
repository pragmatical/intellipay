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

    vendor_name: str = Field(min_length=1)
    invoice_number: str = Field(min_length=1)
    invoice_date: str = Field(min_length=1)
    due_date: str = Field(min_length=1)
    currency: Currency
    subtotal: Decimal
    tax: Decimal
    total_amount: Decimal
    payment_terms: str = Field(min_length=1)
    line_items: list[LineItem] = Field(min_length=1)


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
