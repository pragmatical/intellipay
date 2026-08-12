import re
import sqlite3
from base64 import b64decode, b64encode
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import TypedDict
from uuid import uuid4

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.errors import GraphInterrupt
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from intellipay.config import Settings
from intellipay.parsing import ParserRegistry
from intellipay.reasoning import ReasoningProvider, create_reasoning_provider
from intellipay.reasoning.models import (
    DecisionCritique,
    DecisionCritiqueRequest,
    ExtractionCritiqueRequest,
    ExtractionDefect,
    ExtractionRepairRequest,
    ExtractionRequest,
    InvoiceCandidate,
)
from intellipay.telemetry import Telemetry, create_telemetry
from intellipay.workflow.models import (
    Finding,
    Outcome,
    PaymentStatus,
    ReasoningTraceEntry,
    ReviewAction,
    ReviewCase,
    WorkflowResult,
)
from intellipay.workflow.storage import SQLiteStore
from intellipay.workflow.validation import validate_invoice


class WorkflowState(TypedDict, total=False):
    run_id: str
    source_hash: str
    document_id: str
    content: str
    source_base64: str
    invoice: InvoiceCandidate
    findings: list[Finding]
    extraction_defects: list[ExtractionDefect]
    repair_attempts: int
    reasoning_failure: str | None
    reasoning_trace: list[ReasoningTraceEntry]
    inventory_snapshot: dict[str, str]
    policy_rules_fired: list[str]
    payment_authorized: bool
    outcome: Outcome
    payment_status: PaymentStatus
    payment_id: str | None
    payment_replayed: bool
    review_action: ReviewAction | None


class InvoiceWorkflow:
    def __init__(
        self,
        settings: Settings,
        provider: ReasoningProvider | None = None,
        store: SQLiteStore | None = None,
        parsers: ParserRegistry | None = None,
        telemetry: Telemetry | None = None,
    ) -> None:
        self._settings = settings
        self._provider = provider or create_reasoning_provider(settings)
        self._store = store or SQLiteStore(settings.database_path)
        self._parsers = parsers or ParserRegistry()
        self._telemetry = telemetry or create_telemetry(settings)
        self._store.initialize()
        self._checkpoint_connection = sqlite3.connect(
            settings.database_path, check_same_thread=False
        )
        self._graph = self._build_graph()

    def process(self, path: Path) -> WorkflowResult:
        started = perf_counter()
        source = path.read_bytes()
        content = source.decode("utf-8", errors="replace")
        source_hash = sha256(source).hexdigest()
        run_id = f"run_{uuid4().hex}"
        with self._telemetry.span(
            "intellipay.invoice.process",
            {
                "intellipay.run.id": run_id,
                "intellipay.document.format": path.suffix.lower().lstrip("."),
                "intellipay.reasoning.mode": self._settings.reasoning_mode,
            },
        ) as span:
            self._store.create_run(run_id, source_hash, self._settings.reasoning_mode)
            inventory_snapshot = self._store.inventory()
            final = self._graph.invoke(
                {
                    "run_id": run_id,
                    "source_hash": source_hash,
                    "document_id": path.name,
                    "content": content,
                    "source_base64": b64encode(source).decode("ascii"),
                    "payment_status": PaymentStatus.NOT_ATTEMPTED,
                    "payment_replayed": False,
                    "extraction_defects": [],
                    "repair_attempts": 0,
                    "reasoning_failure": None,
                    "reasoning_trace": [],
                    "inventory_snapshot": inventory_snapshot,
                    "policy_rules_fired": [],
                    "payment_authorized": False,
                },
                config=self._config(run_id),
            )
            invoice = final["invoice"]
            findings = final["findings"]
            outcome = final["outcome"]
            span.set_attribute("intellipay.route.outcome", outcome)
            span.set_attribute(
                "intellipay.finding.codes", sorted({finding.code for finding in findings})
            )
            self._store.complete_run(run_id, invoice, outcome, findings)
            result = self._to_result(final)
        self._telemetry.record_run(
            outcome=outcome,
            reasoning_mode=self._settings.reasoning_mode,
            duration_ms=(perf_counter() - started) * 1000,
        )
        return result

    def resume(self, run_id: str) -> WorkflowResult:
        final = self._graph.invoke(None, config=self._config(run_id))
        if not final:
            raise ValueError(f"No checkpoint exists for run {run_id}")
        return self._to_result(final)

    def resolve_review(
        self,
        review_task_id: str,
        *,
        action: ReviewAction,
        actor: str,
        rationale: str,
    ) -> WorkflowResult:
        existing = self._store.get_review_task(review_task_id)
        with self._telemetry.span(
            "intellipay.review.resolve",
            {
                "intellipay.run.id": existing.run_id,
                "intellipay.review.action": action,
            },
        ):
            task = self._store.decide_review(
                review_task_id,
                action=action,
                actor=actor,
                rationale=rationale,
            )
            if existing.status == "COMPLETED":
                snapshot = self._graph.get_state(self._config(task.run_id))
                if not snapshot.values:
                    raise ValueError(f"No checkpoint exists for run {task.run_id}")
                if "human_review" in snapshot.next:
                    final = self._graph.invoke(
                        Command(resume={"action": task.action}),
                        config=self._config(task.run_id),
                    )
                    if not final:
                        raise RuntimeError(f"Review did not resume run {task.run_id}")
                    self._store.complete_run(
                        task.run_id,
                        final["invoice"],
                        final["outcome"],
                        final["findings"],
                    )
                    return self._to_result(final)
                return self._to_result(snapshot.values)
            final = self._graph.invoke(
                Command(resume={"action": action}),
                config=self._config(task.run_id),
            )
            if not final:
                raise RuntimeError(f"Review did not resume run {task.run_id}")
            self._store.complete_run(
                task.run_id,
                final["invoice"],
                final["outcome"],
                final["findings"],
            )
            return self._to_result(final)

    def review_case(self, review_task_id: str) -> ReviewCase:
        task = self._store.get_review_task(review_task_id)
        snapshot = self._graph.get_state(self._config(task.run_id))
        if not snapshot.values:
            raise ValueError(f"No checkpoint exists for run {task.run_id}")
        state = snapshot.values
        document_id = state["document_id"]
        source_text = None if Path(document_id).suffix.lower() == ".pdf" else state["content"]
        extraction_event = next(
            (
                event
                for event in self._store.events(task.run_id)
                if event.event_type == "invoice_extracted"
            ),
            None,
        )
        extraction_assurance = (
            "Deterministic adapter"
            if extraction_event and extraction_event.payload.get("provider") == "deterministic"
            else "Schema-validated reasoning"
        )
        return ReviewCase(
            task=task,
            document_id=document_id,
            source_hash=state["source_hash"],
            source_text=source_text,
            extraction_assurance=extraction_assurance,
            invoice=state["invoice"],
            findings=state["findings"],
            extraction_defects=state["extraction_defects"],
            policy_rules_fired=state["policy_rules_fired"],
            reasoning_trace=state["reasoning_trace"],
            events=self._store.events(task.run_id),
        )

    def review_source(self, review_task_id: str) -> tuple[str, bytes]:
        task = self._store.get_review_task(review_task_id)
        snapshot = self._graph.get_state(self._config(task.run_id))
        if not snapshot.values:
            raise ValueError(f"No checkpoint exists for run {task.run_id}")
        state = snapshot.values
        return state["document_id"], b64decode(state["source_base64"])

    def _to_result(self, final: WorkflowState) -> WorkflowResult:
        run_id = final["run_id"]
        return WorkflowResult(
            run_id=run_id,
            source_hash=final["source_hash"],
            reasoning_mode=self._settings.reasoning_mode,
            invoice=final["invoice"],
            outcome=final["outcome"],
            findings=final["findings"],
            extraction_defects=final["extraction_defects"],
            repair_attempts=final["repair_attempts"],
            reasoning_trace=final["reasoning_trace"],
            inventory_snapshot=final["inventory_snapshot"],
            policy_rules_fired=final["policy_rules_fired"],
            event_types=self._store.event_types(run_id),
            payment_authorized=final["payment_authorized"],
            payment_status=final["payment_status"],
            payment_id=final.get("payment_id"),
            payment_replayed=final["payment_replayed"],
        )

    def _build_graph(self):
        builder = StateGraph(WorkflowState)
        builder.add_node("extract", self._observed_node("extract", self._extract))
        builder.add_node("validate", self._observed_node("validate", self._validate))
        builder.add_node(
            "critique_extraction",
            self._observed_node("critique_extraction", self._critique_extraction),
        )
        builder.add_node(
            "repair_extraction",
            self._observed_node("repair_extraction", self._repair_extraction),
        )
        builder.add_node("decide", self._observed_node("decide", self._decide))
        builder.add_node(
            "critique_decision",
            self._observed_node("critique_decision", self._critique_decision),
        )
        builder.add_node("human_review", self._observed_node("human_review", self._human_review))
        builder.add_node(
            "authorize_payment",
            self._observed_node("authorize_payment", self._authorize_payment),
        )
        builder.add_node("pay", self._observed_node("pay", self._pay))
        builder.add_edge(START, "extract")
        builder.add_edge("extract", "validate")
        builder.add_conditional_edges(
            "validate",
            self._route_after_validation,
            {"repair": "critique_extraction", "decide": "decide"},
        )
        builder.add_edge("critique_extraction", "repair_extraction")
        builder.add_edge("repair_extraction", "validate")
        builder.add_edge("decide", "critique_decision")
        builder.add_conditional_edges(
            "critique_decision",
            self._route_after_decision,
            {"authorize": "authorize_payment", "review": "human_review", "finish": END},
        )
        builder.add_conditional_edges(
            "human_review",
            self._route_after_review,
            {"authorize": "authorize_payment", "finish": END},
        )
        builder.add_edge("authorize_payment", "pay")
        builder.add_edge("pay", END)
        serializer = JsonPlusSerializer(
            allowed_msgpack_modules=[
                ("intellipay.reasoning.models", "Currency"),
                ("intellipay.reasoning.models", "ExtractionDefect"),
                ("intellipay.reasoning.models", "InvoiceCandidate"),
                ("intellipay.reasoning.models", "LineItem"),
                ("intellipay.workflow.models", "Finding"),
                ("intellipay.workflow.models", "Outcome"),
                ("intellipay.workflow.models", "PaymentStatus"),
                ("intellipay.workflow.models", "ReasoningTraceEntry"),
                ("intellipay.workflow.models", "ReviewAction"),
            ]
        )
        return builder.compile(
            checkpointer=SqliteSaver(self._checkpoint_connection, serde=serializer)
        )

    def _observed_node(self, name: str, node):
        def observed(state: WorkflowState) -> dict[str, object]:
            started = perf_counter()
            status = "SUCCEEDED"
            non_error_exceptions = (GraphInterrupt,) if name == "human_review" else ()
            try:
                with self._telemetry.span(
                    f"intellipay.node.{name}",
                    {
                        "intellipay.run.id": state["run_id"],
                        "intellipay.graph.node": name,
                    },
                    non_error_exceptions=non_error_exceptions,
                ):
                    return node(state)
            except GraphInterrupt:
                status = "INTERRUPTED"
                raise
            except Exception:
                status = "FAILED"
                raise
            finally:
                self._telemetry.record_node(
                    node=name,
                    status=status,
                    duration_ms=(perf_counter() - started) * 1000,
                )

        observed.__name__ = name
        return observed

    def _extract(self, state: WorkflowState) -> dict[str, object]:
        path = Path(state["document_id"])
        has_ambiguous_money = (
            path.suffix.lower() == ".txt"
            and "Invoice Number:" in state["content"]
            and "Vendor:" in state["content"]
            and re.search(r"\$[\d,O.]*O[\d,O.]*", state["content"])
        )
        if self._parsers.supports(path) and not has_ambiguous_money:
            candidate = self._parsers.parse(path, b64decode(state["source_base64"]))
            self._store.record_event(
                state["run_id"],
                "invoice_extracted",
                {"provider": "deterministic", "model": f"{path.suffix[1:]}-v1"},
            )
            return {"invoice": candidate}
        request = ExtractionRequest(document_id=state["document_id"], content=state["content"])
        started = perf_counter()
        try:
            with self._reasoning_span(state, "extract", attempt=0) as span:
                result = self._provider.extract_invoice(request)
                candidate = InvoiceCandidate.model_validate(result.candidate)
                span.set_attribute("gen_ai.request.model", result.model)
        except Exception as error:
            if not self._parsers.supports(path):
                raise
            candidate = self._parsers.parse(path, b64decode(state["source_base64"]))
            trace = self._reasoning_trace(
                operation="extract",
                attempt=0,
                status="FAILED_FALLBACK",
                request=request,
                started=started,
                error=error,
            )
            self._store.record_event(
                state["run_id"],
                "reasoning_failed",
                trace.model_dump(mode="json"),
            )
            return {
                "invoice": candidate,
                "reasoning_failure": self._reasoning_failure_code(error),
                "reasoning_trace": [*state["reasoning_trace"], trace],
            }
        trace = self._reasoning_trace(
            operation="extract",
            attempt=0,
            status="SUCCEEDED",
            request=request,
            started=started,
            model=result.model,
        )
        self._store.record_event(
            state["run_id"],
            "invoice_extracted",
            {"provider": result.provider, "model": result.model},
        )
        return {
            "invoice": candidate,
            "reasoning_trace": [*state["reasoning_trace"], trace],
        }

    def _validate(self, state: WorkflowState) -> dict[str, object]:
        findings = validate_invoice(state["invoice"], state["inventory_snapshot"])
        if state.get("reasoning_failure"):
            findings.append(
                Finding(
                    code=state["reasoning_failure"],
                    message="Reasoning did not produce a verified extraction",
                )
            )
        repairable = {"SUBTOTAL_MISMATCH", "TOTAL_MISMATCH"}
        finding_codes = {finding.code for finding in findings}
        if (
            finding_codes & repairable
            and state["repair_attempts"] >= self._settings.max_extraction_repair_attempts
            and not state.get("reasoning_failure")
        ):
            findings.append(
                Finding(
                    code="REPAIR_EXHAUSTED",
                    message="Extraction defects remain after the configured repair limit",
                )
            )
        prior_relation = self._store.prior_invoice_relation(state["invoice"], state["source_hash"])
        if prior_relation:
            findings.append(
                Finding(
                    code=prior_relation,
                    message=(
                        f"A different document already exists for {state['invoice'].invoice_number}"
                    ),
                )
            )
        self._store.record_event(
            state["run_id"],
            "invoice_validated",
            {"finding_codes": [finding.code for finding in findings]},
        )
        return {"findings": findings}

    def _decide(self, state: WorkflowState) -> dict[str, object]:
        hard_findings = {
            "INVALID_QUANTITY",
            "INVALID_UNIT_PRICE",
            "MISSING_REQUIRED_FIELD",
            "SUBTOTAL_MISMATCH",
            "TOTAL_MISMATCH",
        }
        finding_codes = {finding.code for finding in state["findings"]}
        reasoning_escalations = {
            "MODEL_UNAVAILABLE",
            "MODEL_OUTPUT_INVALID",
            "REPAIR_EXHAUSTED",
        }
        if finding_codes & reasoning_escalations:
            outcome = Outcome.ESCALATE
            policy_rules = ["REASONING_UNCERTAINTY_ESCALATE"]
        elif finding_codes & hard_findings:
            outcome = Outcome.REJECT
            policy_rules = ["HARD_FINDING_REJECT"]
        elif finding_codes:
            outcome = Outcome.ESCALATE
            policy_rules = ["REVIEW_FINDING_ESCALATE"]
        else:
            outcome = Outcome.APPROVE
            policy_rules = ["NO_HARD_FINDINGS"]
        self._store.record_event(
            state["run_id"],
            "invoice_decided",
            {"outcome": outcome, "policy_rules": policy_rules},
        )
        return {"outcome": outcome, "policy_rules_fired": policy_rules}

    def _authorize_payment(self, state: WorkflowState) -> dict[str, object]:
        authorized = state["outcome"] is Outcome.APPROVE and not state["findings"]
        self._store.record_event(state["run_id"], "payment_authorized", {"authorized": authorized})
        return {
            "payment_authorized": authorized,
            "policy_rules_fired": [*state["policy_rules_fired"], "PAYMENT_AUTHORIZED"],
        }

    def _human_review(self, state: WorkflowState) -> dict[str, object]:
        decision = interrupt(
            {
                "run_id": state["run_id"],
                "invoice_number": state["invoice"].invoice_number,
                "finding_codes": [finding.code for finding in state["findings"]],
            }
        )
        action = ReviewAction(decision["action"])
        if action is ReviewAction.APPROVE:
            return {
                "outcome": Outcome.APPROVE,
                "findings": [],
                "review_action": action,
                "policy_rules_fired": [
                    *state["policy_rules_fired"],
                    "HUMAN_REVIEW_APPROVED",
                ],
            }
        policy_rule = (
            "HUMAN_REVIEW_REJECTED"
            if action is ReviewAction.REJECT
            else "HUMAN_CORRECTION_REQUESTED"
        )
        return {
            "outcome": Outcome.REJECT,
            "review_action": action,
            "policy_rules_fired": [*state["policy_rules_fired"], policy_rule],
        }

    def _critique_decision(self, state: WorkflowState) -> dict[str, object]:
        finding_codes = [finding.code for finding in state["findings"]]
        if "HIGH_VALUE" not in finding_codes:
            return {}
        request = DecisionCritiqueRequest(
            invoice_number=state["invoice"].invoice_number,
            proposed_outcome=state["outcome"],
            findings=finding_codes,
        )
        started = perf_counter()
        try:
            with self._reasoning_span(state, "critique_decision", attempt=0) as span:
                result = self._provider.critique_decision(request)
                critique = DecisionCritique.model_validate(result.critique)
                span.set_attribute("gen_ai.request.model", result.model)
        except Exception as error:
            trace = self._reasoning_trace(
                operation="critique_decision",
                attempt=0,
                status="FAILED_DETERMINISTIC_ROUTE_PRESERVED",
                request=request,
                started=started,
                error=error,
            )
            self._store.record_event(
                state["run_id"], "reasoning_failed", trace.model_dump(mode="json")
            )
            return {"reasoning_trace": [*state["reasoning_trace"], trace]}
        trace = self._reasoning_trace(
            operation="critique_decision",
            attempt=0,
            status="SUCCEEDED_ROUTE_PRESERVED",
            request=request,
            started=started,
            model=result.model,
        )
        self._store.record_event(
            state["run_id"],
            "decision_critiqued",
            {
                "accept_recommendation": critique.accept_recommendation,
                "defect_count": len(critique.defects),
                "outcome_preserved": state["outcome"],
            },
        )
        return {"reasoning_trace": [*state["reasoning_trace"], trace]}

    def _critique_extraction(self, state: WorkflowState) -> dict[str, object]:
        request = ExtractionCritiqueRequest(
            candidate=state["invoice"],
            finding_codes=[finding.code for finding in state["findings"]],
        )
        started = perf_counter()
        try:
            with self._reasoning_span(
                state, "critique_extraction", attempt=state["repair_attempts"]
            ):
                critique = self._provider.critique_extraction(request)
                defects = [ExtractionDefect.model_validate(defect) for defect in critique.defects]
        except Exception as error:
            trace = self._reasoning_trace(
                operation="critique_extraction",
                attempt=state["repair_attempts"],
                status="FAILED",
                request=request,
                started=started,
                error=error,
            )
            self._store.record_event(
                state["run_id"], "reasoning_failed", trace.model_dump(mode="json")
            )
            return {
                "reasoning_failure": self._reasoning_failure_code(error),
                "reasoning_trace": [*state["reasoning_trace"], trace],
            }
        trace = self._reasoning_trace(
            operation="critique_extraction",
            attempt=state["repair_attempts"],
            status="SUCCEEDED",
            request=request,
            started=started,
        )
        self._store.record_event(
            state["run_id"],
            "extraction_critiqued",
            {"defect_codes": [defect.code for defect in defects]},
        )
        return {
            "extraction_defects": defects,
            "reasoning_trace": [*state["reasoning_trace"], trace],
        }

    def _repair_extraction(self, state: WorkflowState) -> dict[str, object]:
        attempt = state["repair_attempts"] + 1
        if state.get("reasoning_failure"):
            return {"repair_attempts": attempt}
        request = ExtractionRepairRequest(
            extraction=ExtractionRequest(
                document_id=state["document_id"], content=state["content"]
            ),
            candidate=state["invoice"],
            defects=state["extraction_defects"],
            attempt=attempt,
        )
        started = perf_counter()
        try:
            with self._reasoning_span(state, "repair_extraction", attempt=attempt) as span:
                result = self._provider.repair_invoice(request)
                candidate = InvoiceCandidate.model_validate(result.candidate)
                span.set_attribute("gen_ai.request.model", result.model)
        except Exception as error:
            trace = self._reasoning_trace(
                operation="repair_extraction",
                attempt=attempt,
                status="FAILED",
                request=request,
                started=started,
                error=error,
            )
            self._store.record_event(
                state["run_id"], "reasoning_failed", trace.model_dump(mode="json")
            )
            return {
                "repair_attempts": attempt,
                "reasoning_failure": self._reasoning_failure_code(error),
                "reasoning_trace": [*state["reasoning_trace"], trace],
            }
        trace = self._reasoning_trace(
            operation="repair_extraction",
            attempt=attempt,
            status="SUCCEEDED",
            request=request,
            started=started,
            model=result.model,
        )
        self._store.record_event(state["run_id"], "extraction_repaired", {"attempt": attempt})
        return {
            "invoice": candidate,
            "repair_attempts": attempt,
            "reasoning_trace": [*state["reasoning_trace"], trace],
        }

    def _pay(self, state: WorkflowState) -> dict[str, object]:
        if not state["payment_authorized"]:
            raise RuntimeError("Payment requires explicit authorization")
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
        self._telemetry.record_payment(status=status, replayed=replayed)
        return {
            "payment_id": payment_id,
            "payment_status": status,
            "payment_replayed": replayed,
        }

    @staticmethod
    def _route_after_decision(state: WorkflowState) -> str:
        if state["outcome"] is Outcome.APPROVE:
            return "authorize"
        return "review" if state["outcome"] is Outcome.ESCALATE else "finish"

    @staticmethod
    def _route_after_review(state: WorkflowState) -> str:
        return "authorize" if state["outcome"] is Outcome.APPROVE else "finish"

    def _route_after_validation(self, state: WorkflowState) -> str:
        repairable = {"SUBTOTAL_MISMATCH", "TOTAL_MISMATCH"}
        finding_codes = {finding.code for finding in state["findings"]}
        return (
            "repair"
            if finding_codes
            and finding_codes <= repairable
            and state["repair_attempts"] < self._settings.max_extraction_repair_attempts
            else "decide"
        )

    def _reasoning_trace(
        self,
        *,
        operation: str,
        attempt: int,
        status: str,
        request: object,
        started: float,
        model: str | None = None,
        error: Exception | None = None,
    ) -> ReasoningTraceEntry:
        request_json = (
            request.model_dump_json() if hasattr(request, "model_dump_json") else repr(request)
        )
        trace_entry = ReasoningTraceEntry(
            operation=operation,
            attempt=attempt,
            status=status,
            provider=self._settings.reasoning_mode,
            model=model,
            prompt_version="reasoning-v1",
            latency_ms=max(0, round((perf_counter() - started) * 1000)),
            request_fingerprint=sha256(request_json.encode()).hexdigest(),
            error_type=type(error).__name__ if error else None,
        )
        self._telemetry.record_reasoning(
            operation=operation,
            provider=self._settings.reasoning_mode,
            status=status,
            duration_ms=trace_entry.latency_ms,
        )
        return trace_entry

    def _reasoning_span(self, state: WorkflowState, operation: str, *, attempt: int):
        return self._telemetry.span(
            f"intellipay.reasoning.{operation}",
            {
                "intellipay.run.id": state["run_id"],
                "intellipay.repair.attempt": attempt,
                "gen_ai.operation.name": operation,
                "gen_ai.system": self._settings.reasoning_mode,
            },
        )

    @staticmethod
    def _reasoning_failure_code(error: Exception) -> str:
        return (
            "MODEL_OUTPUT_INVALID"
            if error.__class__.__module__.startswith("pydantic")
            else "MODEL_UNAVAILABLE"
        )

    @staticmethod
    def _config(run_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": run_id}}
