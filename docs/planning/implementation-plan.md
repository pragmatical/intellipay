# Functional MVP Implementation Plan

## Objective

Deliver a local, reproducible IntelliPay MVP that processes every supplied invoice through ingestion, extraction, validation, approval, human review when required, and idempotent mock payment. The MVP must demonstrate deterministic controls, bounded Grok reasoning, safe offline behavior, explainable outcomes, and replay-safe side effects.

This plan starts from the current repository state: analysis, architecture, ADRs, invoice fixtures, and evaluation requirements exist; the Python application, persistence, UI, evaluation assets, and automated tests do not.

## Functional MVP Definition

The MVP is complete when:

1. A documented command processes any supplied invoice from a clean local setup.
2. Every supplied invoice reaches `APPROVE`, `REJECT`, or `ESCALATE` with a structured trace.
3. Known formats use deterministic extraction before model fallback.
4. Labeled integrity, inventory, duplicate, revision, amount, and currency conditions produce expected findings and routes.
5. Ambiguous extraction can use a structured reasoning provider, one bounded repair loop, and safe escalation.
6. A reviewer can inspect evidence and record an allowed decision for an escalated case.
7. Only an authorized, idempotent command can invoke mock payment.
8. Reprocessing or replay cannot create a second payment.
9. The default test and evaluation suites run offline with deterministic model fixtures.
10. The prototype quality gates in the [evaluation approach](../analysis/evaluation-approach.md#prototype-acceptance) pass.

## Delivery Strategy

Build thin vertical behavior first, then expand by risk. Each phase must leave the repository runnable and must satisfy its exit gate before work begins on the next phase, except for documentation or fixtures that unblock the current phase.

```mermaid
flowchart LR
    P0[0. Foundation] --> P1[1. Deterministic Slice]
    P1 --> P2[2. Corpus Controls]
    P2 --> P3[3. Bounded Grok]
    P3 --> P4[4. Review and Evidence]
    P4 --> P5[5. MVP Hardening]
```

## Phase 0: Project Foundation

### Goal

Create a reproducible Python project with stable domain contracts and a testable dependency boundary.

### Deliverables

- `pyproject.toml` with locked runtime and development dependencies
- `src/intellipay/` package and CLI entry point
- Configuration model for database path, reasoning mode, thresholds, retry limits, and feature flags
- Canonical typed models for invoices, line items, evidence, findings, decisions, payment commands, and workflow state
- Stable enums or codes for route, severity, finding, and payment status
- Structured logging bootstrap with run and document correlation
- Test layout, reusable fixture factories, and baseline lint, format, type-check, and pytest commands
- SQLite migration mechanism and local database initialization command
- Developer setup and command documentation

### Focused Verification

- Configuration loads with explicit defaults and rejects invalid values.
- Money round-trips as `Decimal`, never binary floating point.
- Domain models serialize to durable graph state without secrets or live connections.
- An empty database can migrate from zero to the latest schema repeatedly.
- A CLI help command and one smoke test run from a clean environment.

### Exit Gate

The package installs, static checks pass, migrations create a local database, and the CLI starts without processing an invoice.

## Phase 1: Deterministic Vertical Slice

### Goal

Process INV-1001 from file intake through deterministic validation and one idempotent mock payment.

### Deliverables

- Intake service that validates the path, limits size, hashes content, detects type, and records source metadata
- Deterministic parser registry with the TXT parser needed by INV-1001
- Canonical schema validation and field evidence for selected parser values
- Seeded SQLite inventory repository using the required case data
- Required-field, quantity, arithmetic, item-existence, and stock checks
- Minimal versioned approval policy for low-risk approval and hard-failure routing
- Payment command, unique idempotency key, mock adapter, and payment ledger
- LangGraph state machine connecting intake, extraction, validation, approval, payment, reconciliation, and terminal nodes
- Structured CLI result and persisted event trace

### Focused Verification

- INV-1001 reaches `APPROVE` and produces one successful mock payment.
- Re-running the same accepted invoice returns or references the existing payment result without a second side effect.
- A synthetic negative quantity reaches `REJECT` and cannot invoke payment.
- Graph-route tests prove validation precedes approval and authorization precedes payment.
- Restarting after a committed node resumes without repeating that node's side effect.

### Demonstration

Run INV-1001, inspect its normalized invoice and rules fired, show the mock payment, then replay it and show duplicate payment prevention.

### Exit Gate

One clean invoice completes end to end, one invalid invoice rejects safely, replay is idempotent, and the focused unit, persistence, graph-route, and end-to-end tests pass offline.

## Phase 2: Full Corpus and Deterministic Controls

### Goal

Support every supplied format and establish expected deterministic findings and routes across the complete seed corpus.

### Deliverables

- JSON, XML, CSV, TXT, and generated PDF extraction adapters
- Normalization for dates, currency, repeated CSV fields, OCR-like values, and line items
- Recalculation of line totals, subtotal, tax, shipping, and grand total with configured tolerance
- Stable findings for missing fields, negative values, unknown items, unavailable stock, quantity mismatch, arithmetic mismatch, unsupported currency, high value, duplicate, and revision ambiguity
- Document, business-identity, revision, and payment-duplicate logic
- Explicit `APPROVE`, `REJECT`, and `ESCALATE` routes with reason codes
- Durable review-task record for escalated cases, without the full review interface
- Versioned evaluation manifest, gold invoices, gold findings, gold routes, and expected side effects for all supplied cases
- Parameterized end-to-end corpus suite and machine-readable result output

### Focused Verification

- Every supplied document parses or reaches an explicit supported escalation.
- INV-1009 hard-fails for negative or missing values and cannot pay.
- INV-1002, INV-1005, and INV-1007 produce inventory and high-value findings.
- INV-1003, INV-1008, and INV-1016 cannot invent catalog mappings or reach payment.
- INV-1004 and its revision are linked and cannot both produce payment.
- INV-1014 preserves EUR and escalates when currency policy is unresolved.
- Gold asset schemas validate before the corpus test runs.

### Demonstration

Run the corpus evaluation and inspect one approved, one rejected, one escalated, one revision-linked, and one unsupported-policy case.

### Exit Gate

All supplied invoices reach their approved gold route or a documented draft-label discrepancy. Hard-control recall is 100% on approved seed labels, payment invariants pass, and per-case failures are reported without stopping the batch.

## Phase 3: Bounded Grok Reasoning

### Goal

Add observable model-assisted extraction and critique without weakening deterministic controls or offline operation.

### Deliverables

- Narrow `ReasoningProvider` protocol for structured extraction and bounded decision critique
- Deterministic fake provider for default tests and demonstrations without network access
- Optional xAI Grok adapter with configurable endpoint, model, timeout, retries, and credentials
- Prompt templates that delimit invoice text as untrusted data
- Strict response schemas and model-output validation
- Extraction critic that emits machine-readable defects such as total mismatch, missing evidence, and invalid date
- One configured bounded repair loop followed by acceptance or escalation
- One-pass enhanced-review critique that may make a recommendation stricter but cannot weaken hard findings
- Recorded prompt, model, attempt, latency, token, and redacted request/response metadata
- Opt-in live-model contract and regression suite separated from offline CI

### Focused Verification

- A fake-provider ambiguous case fails first-pass checks, receives typed defects, repairs successfully, and proceeds.
- An unresolved repair exhausts its attempt limit and reaches review.
- Invalid model JSON and schema output cannot enter accepted workflow state.
- Embedded instructions cannot change tools, policy, routes, or payment authorization.
- Grok timeout or absence follows the defined deterministic fallback or escalation route without data loss.
- The same graph safety tests pass with fake and live adapters.

### Demonstration

Process an OCR-damaged or ambiguous case and show the first candidate, critic defects, bounded repair, deterministic revalidation, and final route. Repeat in offline mode to show safe fallback.

### Exit Gate

The self-correction and unavailable-model paths are executable and traced, no adversarial fixture alters a protected boundary, offline CI remains deterministic, and live-model use is optional.

## Phase 4: Human Review, Evidence, and Observability

### Goal

Provide a usable review workflow and enough evidence and telemetry to understand every route without reading raw logs.

### Deliverables

- LangGraph interrupt and authenticated review-decision contract
- Durable review queue with status, reason, priority, timestamps, and disposition
- Lightweight review interface showing source content, canonical fields, evidence, confidence, findings, policy rules, revision history, and event timeline
- Clear approve, reject, and request-correction actions limited by policy
- Resume flow that records the human actor and continues from the checkpoint without repeating prior work
- Structured event coverage for node start/end, attempts, findings, routes, model calls, review, payment, and reconciliation
- Evaluation report generator for case outcomes, extraction accuracy, finding metrics, route distribution, latency, model use, and payment safety
- Redaction of secrets and unnecessary sensitive content from normal telemetry

### Focused Verification

- An escalated invoice appears in the review queue with understandable reasons.
- A permitted review action resumes the same run and records actor and rationale.
- Disallowed actions are disabled and explained.
- Refreshing or resubmitting a review action does not duplicate the decision or payment.
- Reviewers can answer the four usability questions in the [evaluation approach](../analysis/evaluation-approach.md#human-evaluation) without inspecting logs.
- Empty, loading, error, escalated, and completed states render without overlapping or missing controls.

### Demonstration

Open an escalated invoice, compare source evidence with normalized fields, inspect rules fired, record a decision, and follow the resumed run to its allowed terminal state.

### Exit Gate

The review workflow operates end to end, interrupt and resume tests pass, telemetry is sufficient to reconstruct each supplied case, and a short usability check identifies no blocking comprehension or action errors.

## Phase 5: MVP Hardening and Acceptance

### Goal

Close safety, resilience, usability, documentation, and reproducibility gaps and produce a release candidate that satisfies the functional MVP definition.

### Deliverables

- Mutation fixtures for OCR swaps, removed fields, changed totals, duplicate submissions, currency changes, and prompt injection
- Fault injection for model errors, SQLite locks, process restart, payment timeout, and unknown payment result
- Reconciliation behavior that queries by idempotency identity and never resubmits blindly
- Performance and cost measurements for representative local batches
- Clean-clone setup, migration, run, review, evaluation, and troubleshooting instructions
- Versioned evaluation report with overall and segmented metrics plus per-case failures
- Security and privacy review of secrets, untrusted input, logs, model payloads, and local persistence
- Known limitations and unresolved business-policy decisions
- Functional MVP release tag or equivalent immutable version identifier

### Focused Verification

- The complete offline suite passes from a clean environment.
- Every supplied invoice reaches its expected state with a complete trace.
- Payment and graph safety invariants pass at 100%.
- Hard-control recall is 100% on approved seed labels.
- Required-field accuracy reaches the approved prototype threshold.
- No prompt-injection case changes route, policy, tool permissions, or payment authorization.
- Every injected model and payment outage reaches its defined safe state.
- Desktop and mobile review workflows complete without blocking layout or interaction defects.

### Demonstration

Run the complete acceptance suite and evaluation report, then demonstrate a routine approval, deterministic rejection, model-assisted repair, human escalation, and replay-protected payment.

### Exit Gate

All Functional MVP Definition items and prototype quality gates pass, no critical defect remains open, setup is reproducible, and unresolved policy choices are explicit rather than encoded as permissive defaults.

## Cross-Phase Workstreams

### Testing and Evaluation

- Add focused tests with each behavior rather than deferring coverage to Phase 5.
- Keep the default suite deterministic and offline.
- Version gold labels independently from test implementation.
- Convert every defect into a minimal permanent regression fixture.

### Security and Privacy

- Treat file names, document content, parser output, and model output as untrusted from Phase 1.
- Keep secrets out of graph state, fixtures, logs, and evaluation reports.
- Parameterize SQL and restrict repositories and tools by responsibility.
- Redact routine telemetry before adding live-model use or a reviewer interface.

### Documentation and Decisions

- Update commands and behavior as each phase becomes executable.
- Keep architecture diagrams and ADRs aligned with implemented boundaries.
- Create or supersede an ADR when implementation requires a materially different architectural choice.
- Keep production concerns documented but outside the MVP unless required by a safety gate.

### Observability

- Establish run and document correlation in Phase 0.
- Add node duration, attempt, finding, and route events alongside each graph node.
- Add model and payment metadata only at their controlled boundaries.
- Prefer stable structured fields over prose-only logs.

## Dependencies and Decision Needs

| Needed by | Dependency or decision | Owner |
|---|---|---|
| Phase 1 | Confirm prototype policy that permits INV-1001 auto-approval | Finance or product owner |
| Phase 2 | Approve seed gold routes and inventory-shortage interpretation | Finance and inventory owner |
| Phase 2 | Define arithmetic and amount tolerances used by deterministic rules | Finance |
| Phase 3 | Provide optional xAI credentials and approve model data handling | Security and solution owner |
| Phase 4 | Define reviewer identity for the local prototype and allowed actions | Product and finance |
| Phase 5 | Approve critical fields and prototype accuracy thresholds | Finance and product owner |

Until an owner resolves a business-policy dependency, route affected invoices to `ESCALATE`; do not invent a permissive default.

## Risks and Mitigations

| Risk | Effect on MVP | Mitigation |
|---|---|---|
| Parser breadth delays the first runnable path | Functionality remains invisible | Complete INV-1001 vertical slice before adding formats |
| Gold routes encode unapproved policy assumptions | Tests institutionalize the wrong behavior | Track label status and escalate unresolved cases |
| Model integration becomes the critical path | Offline workflow and tests stall | Ship deterministic core and fake provider first |
| Evidence schema becomes production-grade too early | Persistence work crowds out user value | Implement the minimum evidence contract from ADR-0005 |
| Review UI becomes a broad product surface | MVP delivery expands without improving controls | Build one evidence-first queue and detail workflow |
| Retries duplicate payment | Direct financial safety failure | Persist command identity before invocation and reconcile unknown outcomes |
| Full corpus passes while weak segments are hidden | Aggregate metrics give false confidence | Report per-case and segmented metrics with quality gates |

## Explicitly Outside the Functional MVP

- Real bank or treasury integration
- Autonomous real-money payment
- Enterprise SSO, role provisioning, or multi-tenant authorization
- Production vendor master, purchase order, receipt, contract, tax, or FX integration
- Distributed workers, managed queues, object storage, or managed database deployment
- Automatic model training from reviewer actions
- Production-scale retention, residency, archival, availability, and recovery controls

## Related Documents

- [Business case analysis](../analysis/business-case-analysis.md)
- [Proposed solution](../analysis/proposed-solution.md)
- [Architecture](../analysis/architecture.md)
- [Evaluation approach and needs](../analysis/evaluation-approach.md)
- [Architecture decision records](../adr/0001-use-langgraph-state-machine.md)