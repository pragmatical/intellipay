from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from intellipay.config import ReasoningMode
from intellipay.reasoning.models import InvoiceCandidate


class Outcome(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"


class PaymentStatus(StrEnum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    SUCCESS = "SUCCESS"


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)


class WorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    source_hash: str
    reasoning_mode: ReasoningMode
    invoice: InvoiceCandidate
    outcome: Outcome
    findings: list[Finding]
    payment_status: PaymentStatus
    payment_id: str | None = None
    payment_replayed: bool = False
