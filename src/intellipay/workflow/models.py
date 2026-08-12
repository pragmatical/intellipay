from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from intellipay.config import ReasoningMode
from intellipay.reasoning.models import ExtractionDefect, InvoiceCandidate


class Outcome(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"


class PaymentStatus(StrEnum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    SUCCESS = "SUCCESS"


class ReviewAction(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CORRECTION = "REQUEST_CORRECTION"


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ReasoningTraceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: str
    attempt: int = Field(ge=0)
    status: str
    provider: str
    model: str | None = None
    prompt_version: str
    latency_ms: int = Field(ge=0)
    request_fingerprint: str
    token_usage: int | None = Field(default=None, ge=0)
    error_type: str | None = None


class ReviewTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_task_id: str
    run_id: str
    invoice_number: str
    reason_codes: list[str]
    status: str
    priority: str
    created_at: str
    updated_at: str
    allowed_actions: list[ReviewAction]
    action: ReviewAction | None = None
    actor: str | None = None
    rationale: str | None = None
    completed_at: str | None = None


class ReviewEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(ge=1)
    event_id: str
    schema_version: int = Field(ge=1)
    event_type: str
    payload: dict[str, object]
    created_at: str
    trace_id: str | None = None
    span_id: str | None = None


class ReviewCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: ReviewTask
    document_id: str
    source_hash: str
    source_text: str | None
    extraction_assurance: str
    invoice: InvoiceCandidate
    findings: list[Finding]
    extraction_defects: list[ExtractionDefect]
    policy_rules_fired: list[str]
    reasoning_trace: list[ReasoningTraceEntry]
    events: list[ReviewEvent]


class WorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    source_hash: str
    reasoning_mode: ReasoningMode
    invoice: InvoiceCandidate
    outcome: Outcome
    findings: list[Finding]
    extraction_defects: list[ExtractionDefect] = Field(default_factory=list)
    repair_attempts: int = 0
    reasoning_trace: list[ReasoningTraceEntry] = Field(default_factory=list)
    inventory_snapshot: dict[str, str]
    policy_rules_fired: list[str]
    event_types: list[str]
    payment_authorized: bool = False
    payment_status: PaymentStatus
    payment_id: str | None = None
    payment_replayed: bool = False
