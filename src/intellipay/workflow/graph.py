from hashlib import sha256
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from intellipay.config import Settings
from intellipay.reasoning import ReasoningProvider, create_reasoning_provider
from intellipay.reasoning.models import ExtractionRequest, InvoiceCandidate
from intellipay.workflow.models import Finding, Outcome, PaymentStatus, WorkflowResult
from intellipay.workflow.storage import SQLiteStore
from intellipay.workflow.validation import validate_invoice


class WorkflowState(TypedDict, total=False):
    run_id: str
    source_hash: str
    document_id: str
    content: str
    invoice: InvoiceCandidate
    findings: list[Finding]
    outcome: Outcome
    payment_status: PaymentStatus
    payment_id: str | None
    payment_replayed: bool


class InvoiceWorkflow:
    def __init__(
        self,
        settings: Settings,
        provider: ReasoningProvider | None = None,
        store: SQLiteStore | None = None,
    ) -> None:
        self._settings = settings
        self._provider = provider or create_reasoning_provider(settings)
        self._store = store or SQLiteStore(settings.database_path)
        self._store.initialize()
        self._graph = self._build_graph()

    def process(self, path: Path) -> WorkflowResult:
        content = path.read_text(encoding="utf-8")
        source_hash = sha256(content.encode()).hexdigest()
        run_id = f"run_{uuid4().hex}"
        self._store.create_run(run_id, source_hash, self._settings.reasoning_mode)
        final = self._graph.invoke(
            {
                "run_id": run_id,
                "source_hash": source_hash,
                "document_id": path.name,
                "content": content,
                "payment_status": PaymentStatus.NOT_ATTEMPTED,
                "payment_replayed": False,
            }
        )
        invoice = final["invoice"]
        findings = final["findings"]
        outcome = final["outcome"]
        self._store.complete_run(run_id, invoice, outcome, findings)
        return WorkflowResult(
            run_id=run_id,
            source_hash=source_hash,
            reasoning_mode=self._settings.reasoning_mode,
            invoice=invoice,
            outcome=outcome,
            findings=findings,
            payment_status=final["payment_status"],
            payment_id=final.get("payment_id"),
            payment_replayed=final["payment_replayed"],
        )

    def _build_graph(self):
        builder = StateGraph(WorkflowState)
        builder.add_node("extract", self._extract)
        builder.add_node("validate", self._validate)
        builder.add_node("decide", self._decide)
        builder.add_node("pay", self._pay)
        builder.add_edge(START, "extract")
        builder.add_edge("extract", "validate")
        builder.add_edge("validate", "decide")
        builder.add_conditional_edges(
            "decide", self._route_after_decision, {"pay": "pay", "finish": END}
        )
        builder.add_edge("pay", END)
        return builder.compile()

    def _extract(self, state: WorkflowState) -> dict[str, object]:
        result = self._provider.extract_invoice(
            ExtractionRequest(document_id=state["document_id"], content=state["content"])
        )
        self._store.record_event(
            state["run_id"],
            "invoice_extracted",
            {"provider": result.provider, "model": result.model},
        )
        return {"invoice": result.candidate}

    def _validate(self, state: WorkflowState) -> dict[str, object]:
        findings = validate_invoice(state["invoice"], self._store.inventory())
        self._store.record_event(
            state["run_id"],
            "invoice_validated",
            {"finding_codes": [finding.code for finding in findings]},
        )
        return {"findings": findings}

    def _decide(self, state: WorkflowState) -> dict[str, object]:
        outcome = Outcome.REJECT if state["findings"] else Outcome.APPROVE
        self._store.record_event(state["run_id"], "invoice_decided", {"outcome": outcome})
        return {"outcome": outcome}

    def _pay(self, state: WorkflowState) -> dict[str, object]:
        invoice = state["invoice"]
        idempotency_key = sha256(
            f"{invoice.invoice_number}|{invoice.vendor_name}|{invoice.total_amount}".encode()
        ).hexdigest()
        payment_id, status, replayed = self._store.record_payment(idempotency_key, invoice)
        self._store.record_event(
            state["run_id"],
            "payment_recorded",
            {"payment_id": payment_id, "status": status, "replayed": replayed},
        )
        return {
            "payment_id": payment_id,
            "payment_status": status,
            "payment_replayed": replayed,
        }

    @staticmethod
    def _route_after_decision(state: WorkflowState) -> str:
        return "pay" if state["outcome"] is Outcome.APPROVE else "finish"
