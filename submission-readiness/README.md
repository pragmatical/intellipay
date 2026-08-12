# Submission Readiness

## Purpose and Boundary

This directory validates how well the repository demonstrates the criteria by which the exercise will be graded. It is an internal assessment and delivery-governance area, not part of the IntelliPay solution, product architecture, runtime, or user documentation.

The separation is intentional:

- `docs/`, application code, tests, and the root project README describe or implement the solution.
- `submission-readiness/` assesses the evidence produced by those artifacts against the external evaluation rubric.
- Readiness guidance may prioritize work, but it must not become a runtime dependency or distort solution documentation into scoring commentary.
- Claims in this directory do not count as proof. Only repeatable application behavior, tests, traces, reports, screenshots, and observed user flows can demonstrate a criterion.

The grading criteria originate in [the supplied exercise context](../context/README.md#evaluation-criteria). This assessment should be updated as implementation evidence changes and may be excluded from product-facing documentation or deliverables if required.

Assessment date: 2026-08-12

## Executive Assessment

IntelliPay now has a runnable application, typed LangGraph workflow, deterministic multi-format corpus processing, bounded model reasoning, durable human review, and idempotent mock payment. The complete offline suite passes 52 tests, and the 20-case corpus report shows full route and finding agreement, full hard-control recall, and zero prohibited payments. Functionality, Code Quality, Agentic Sophistication, Shipping Mindset, Above/Beyond, and UI/UX have repeatable evidence.

The main submission gap is now presentation and release evidence rather than core implementation. The repository lacks a concise golden-demo script or recording, a screenshot set, a clean-environment acceptance transcript, consolidated performance/cost results, and a single limitations/security review. Finance label approval and observed AP usability measures also remain external; completed tabletop simulations must not be presented as participant evidence.

## Scorecards

Status meanings:

- **Demonstrated:** Executable behavior and repeatable evidence exist.
- **Designed:** The repository explains the behavior but cannot prove it yet.
- **Missing:** Neither sufficient design nor executable proof exists.

### Original Readiness Baseline

This table preserves the initial repository assessment for reference. It describes the evidence available before implementation began and is not the current project status.

| Criterion | Status | Existing strength | Primary gap | Proof required |
|---|---|---|---|---|
| Functionality | Designed | Complete workflow, scenario matrix, terminal outcomes, and payment invariants | No runnable CLI, graph, database, or adapters | Run every supplied invoice end to end and show the expected terminal or review state |
| Code Quality | Designed | Typed boundaries, retry policy, trust boundaries, and test strategy | No application code, dependency manifest, tests, or instrumentation | Passing unit, contract, graph-route, and end-to-end tests plus structured logs |
| Agentic Sophistication | Designed | LangGraph flow, narrow tools, Grok provider, extraction critic, and bounded correction loop | No working model adapter, critic loop, tool calls, or trace | Demonstrate structured model output, critic defects, retry, fallback, and policy-safe routing |
| Shipping Mindset | Designed | Local-first scope, SQLite, mock payment, offline path, and explicit production deferrals | Some design exceeds what is needed for the first vertical slice | Deliver the cut line below before generalized lineage or production integrations |
| Presentation | Designed | Business baseline, target outcomes, risk mapping, diagrams, and ADR rationale | No live narrative backed by measured output | Present baseline, decision rationale, live cases, metrics, and business impact in one coherent demo |
| Above/Beyond | Designed | Revision handling, replay safety, policy versioning, adversarial cases, and payment idempotency | Differentiators are not implemented or visible | Make at least revision safety, prompt-injection resistance, and replay idempotency executable |
| UI/UX | Designed | A structured result contract and reviewer information needs are described | No review screen, status history, or human decision action | Provide a lightweight review console with evidence, findings, reasons, and explicit actions |

### Current Progress

This table assesses the executable evidence currently present in the repository.

| Criterion | Status | Existing strength | Primary gap | Proof required |
|---|---|---|---|---|
| Functionality | Demonstrated | CLI and LangGraph execute approve, reject, escalate, review, and payment routes across all 20 cases | Clean-environment acceptance transcript is not captured | Reproduce setup, corpus evaluation, and representative workflows from a clean checkout |
| Code Quality | Demonstrated | Typed boundaries, dependency injection, durable storage, structured events, and 52 passing tests | No consolidated security review or SQLite lock/process-restart fault evidence | Capture lint/type/test evidence and close or register remaining resilience gaps |
| Agentic Sophistication | Demonstrated | Local and Grok-compatible providers, structured output, critic defects, bounded repair, fallback, prompt-injection isolation, and typed traces | Credentialed live-model behavior remains optional and environment-dependent | Preserve offline evidence; add a redacted live smoke trace only when credentials are approved |
| Shipping Mindset | Demonstrated | Local-first implementation ships the complete core workflow while explicitly deferring production infrastructure | No immutable prototype release identifier | Complete acceptance evidence and tag the demonstrated prototype |
| Presentation | Designed | Business baseline, architecture, ADRs, measured corpus results, and live review UI are available | No concise demo script/recording, screenshots, or consolidated result narrative | Package and rehearse the ten-minute golden demo with reproducible evidence |
| Above/Beyond | Demonstrated | Revision safety, equivalent-format identity, prompt-injection resistance, strict checkpoint serialization, and replay idempotency are executable | Differentiators are distributed across tests and verification records | Surface the strongest three in the golden demo |
| UI/UX | Demonstrated | Authenticated queue and detail views expose source, normalized facts, findings, rules, history, rationale, and constrained actions on desktop/mobile | Real AP handling-time, confidence, and comprehension evidence is absent | Run representative AP sessions or explicitly retain this as an external limitation |

## Highest-Leverage Next Actions

1. **Produce the acceptance and resilience evidence pack.** Run setup from a clean checkout; capture tests, lint, formatting, corpus metrics, required-field accuracy, representative traces, model/payment outage behavior, SQLite lock or restart behavior, latency, and model-use/cost summaries. Record unresolved items in one limitations and security review.
2. **Package the golden demo.** Create a ten-minute script covering the business baseline, INV-1001 approval and replay, a bounded repair, INV-1002 review, a hard rejection, revision safety, and measured corpus results. Capture desktop/mobile screenshots and a completed-review state, then rehearse from the documented setup.
3. **Complete external evidence where participants are available.** Obtain authorized finance/domain approval for the 20 `simulated-reviewed` labels and run AP sessions for handling time, confidence, help requests, and comprehension. These improve trust and UI evidence but should remain clearly pending if submission timing does not permit them.

## Current Executable Evidence

- `uv run pytest -q` passes 52 tests.
- `uv run intellipay-evaluate --output evaluation/stage2-report.json` evaluates 20/20 cases with zero errors and zero prohibited payments.
- `uv run intellipay <invoice-path>` demonstrates routine, rejected, and escalated CLI outcomes.
- `uv run intellipay-review --host 0.0.0.0 --port 8000` serves the authenticated review workflow.
- `docs/planning/stage-2-verification.md`, `stage-3-verification.md`, and `stage-4-verification.md` record repeatable focused checks.
- `docs/runbooks/finance-domain-label-approval-simulation.md` and `accounts-payable-usability-simulation.md` record completed simulations and their limitations.

Documentation is not executable proof. Update a status to **Demonstrated** only when a repeatable command, test, screenshot, trace, or recorded metric supports it.

## MVP Cut Line

### Must Ship

1. A Python CLI that accepts one supplied invoice path and returns a structured result.
2. A LangGraph workflow with explicit ingestion, extraction, validation, approval, payment, and terminal routes.
3. Deterministic parsers for JSON, XML, CSV, and known text, with PDF text extraction where generated PDFs are part of the demo.
4. A canonical typed invoice model using `Decimal` for money.
5. SQLite inventory setup using the required seed data and a narrow repository interface.
6. Deterministic integrity, arithmetic, inventory, unknown-item, amount-threshold, duplicate, and revision controls.
7. A `ReasoningProvider` with a deterministic fake and optional xAI adapter.
8. One visible bounded self-correction path: model extraction, machine-readable critic defects, one repair attempt, then accept or escalate.
9. Three explicit outcomes: `APPROVE`, `REJECT`, and `ESCALATE`.
10. Mock payment with a persisted idempotency key and replay protection.
11. Structured logs containing run, node, attempt, route, finding, policy, model, and duration metadata.
12. Automated tests across all supplied invoices, graph safety invariants, offline behavior, prompt injection, and duplicate payment.
13. A lightweight review console showing source content, normalized fields, findings, confidence/evidence, policy reasons, and approve/reject/request-correction actions.

### Implement Minimally

| Capability | Prototype implementation |
|---|---|
| Evidence lineage | Source hash, canonical values, field evidence, producer version, findings, policy/rules fired, decision, and payment result |
| Audit | Structured append-only events sufficient for the demo and evaluation report |
| Reference data | Required inventory table and snapshot hash only |
| Human review | Durable review state plus one reviewer flow; no enterprise identity integration |
| Observability | Structured logs and a generated run summary; no monitoring platform |
| UI | One functional review console optimized for the golden demo; no design system or broad administration surface |

### Defer

- Real banking connectivity and autonomous real-money movement
- Vendor master, purchase order, goods receipt, contract, tax, and live FX integrations
- Generalized lineage graphs, retention automation, tamper-evident event chains, and production archive design
- Multi-tenant authorization, enterprise SSO, queues, distributed workers, and managed infrastructure
- Model training, fine-tuning, or automatic learning from reviewer corrections
- Broad analytics dashboards beyond the evaluation report

## Golden Demo

The presentation should tell one end-to-end story in ten minutes or less.

1. **Baseline:** State the 30% error rate, five-day cycle, and $2M annual loss.
2. **Routine automation:** Process INV-1001 through deterministic extraction, validation, approval, and one mock payment.
3. **Agentic correction:** Process an OCR-damaged or ambiguous invoice such as INV-1012. Show the model candidate, critic defect codes, bounded retry, and accepted or escalated result.
4. **Controlled exception:** Process INV-1002 or INV-1003. Show inventory/high-value findings and prove that model reasoning cannot bypass review or rejection.
5. **Financial safety:** Replay INV-1001 and show that the payment idempotency key prevents a second payment.
6. **Reviewer experience:** Open the review console, inspect source evidence and rules fired, and record a human action.
7. **Measured result:** Show corpus pass count, hard-control recall, extraction accuracy, route distribution, latency, model calls, and duplicate payments prevented.

Keep INV-1004/R1 as the Above/Beyond proof for revision lineage and INV-1009 as the simplest hard-failure proof. Preserve INV-1014 as evidence that unsupported business policy escalates instead of being invented.

## Criterion-Specific Guidance

### Functionality

Optimize for a complete path before parser breadth. The first milestone is INV-1001 from file to mock payment with persisted events. The second is one reject and one escalation. Only then expand to the full corpus.

### Code Quality

Use typed domain models, pure deterministic rules, ports for external dependencies, stable finding codes, and dependency injection for the reasoning and payment adapters. Every graph route and side effect needs a focused test. Log structured facts rather than prose-only messages.

### Agentic Sophistication

Do not maximize the number of agents. Make the existing responsibilities observable and defensible:

- Extraction agent calls only parser and reasoning tools.
- Critic emits typed defects and can request only a bounded repair.
- Validation tools provide facts and never delegate hard controls to the model.
- Approval combines deterministic policy with one bounded critique for enhanced-review cases.
- Model output can make a route stricter but cannot authorize payment or weaken a hard finding.

The trace should visibly show tool input, structured output, defect, retry count, and final route without exposing secrets or unnecessary invoice data.

### Shipping Mindset

Treat the production direction as evidence of judgment, not current scope. Do not implement managed queues, full archival governance, or enterprise integrations until the golden demo and full-corpus tests pass.

### Presentation

Frame each technical choice as a business control:

- Deterministic rules reduce false approvals and make outcomes reproducible.
- Grok reduces manual effort on ambiguous documents without receiving payment authority.
- Escalation converts uncertainty into a manageable queue instead of hidden risk.
- Idempotency prevents duplicate cash movement.
- Evidence and rules fired reduce review time and improve auditability.

### Above/Beyond

Favor features that are easy to demonstrate and reinforce the core story. Revision-safe payment, adversarial prompt-injection tests, deterministic offline operation, and replayable traces are higher value than adding unrelated integrations.

### UI/UX

The review console should answer four questions without requiring log inspection:

1. What did the system extract?
2. What evidence and confidence support it?
3. Which checks and policy rules determined this route?
4. What action is available to me now?

Use clear status labels, field-level differences, finding severity, source excerpts, and a chronological trace. Disable actions that policy does not permit and explain why in plain language.

## Evidence Checklist

Before submission, capture or generate:

- A clean-clone setup and run command
- Test output for the complete suite and the 16-invoice matrix
- A machine-readable evaluation report
- One successful, one rejected, one escalated, and one replay-protected trace
- One self-correction trace with typed critic defects
- One offline model-unavailable trace
- One prompt-injection test proving route and tool isolation
- Screenshots of the review list, invoice detail, evidence/findings, and completed review action
- A concise architecture diagram and the seven ADR links
- A limitations section that names deferred integrations and unresolved business policy

## Reassessment Rule

Reassess this scorecard after each vertical-slice milestone. Rank the next work by the number of weak criteria it improves. For example, a working review console backed by real graph state improves Functionality, UI/UX, Presentation, and Above/Beyond simultaneously; a production retention subsystem does not improve the current weakest criteria.

## Solution References

These links are inputs to the assessment; the linked documents remain solution artifacts and must not contain readiness scoring commentary.

- [Business case analysis](../docs/analysis/business-case-analysis.md)
- [Proposed solution](../docs/analysis/proposed-solution.md)
- [Architecture](../docs/analysis/architecture.md)
- [Solution evaluation approach](../docs/analysis/evaluation-approach.md)
- [Architecture decision records](../docs/adr/0001-use-langgraph-state-machine.md)
