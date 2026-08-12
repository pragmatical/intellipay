# Functional MVP Implementation Plan

## Objective

Deliver a local, reproducible IntelliPay MVP that processes every supplied invoice through ingestion, extraction, validation, approval, human review when required, and idempotent mock payment. The MVP must measurably enforce deterministic controls, bounded Grok reasoning, safe offline behavior, explainable outcomes, and replay-safe side effects.

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

Build the solution as cumulative stages that each produce a measurable operational capability or reduction in risk. A stage is complete only when its stated measures meet their targets and its outcome gate passes; completing implementation tasks or preparing a presentation does not complete a stage.

Each stage defines a measurable outcome, quantitative or binary measures, outcome scope, a repeatable verification procedure, completion evidence, implementation work, and an outcome gate. Foundation work is included in Stage 1 rather than delivered separately. Later stages preserve all earlier measures and gates so progress remains cumulative and regressions are visible.

```mermaid
flowchart LR
    S1[1. One Safe Payment] --> S2[2. Every Seed Case Controlled]
    S2 --> S3[3. Ambiguity Resolved Safely]
    S3 --> S4[4. Exceptions Resolved by Reviewers]
    S4 --> S5[5. MVP Quality Gates Passed]
```

## Stage 1: Produce One Safe, Replay-Protected Payment

### Measurable Outcome

Accounts payable can submit a clean invoice, see the extracted facts and checks performed, receive an approval decision, and execute one safe mock payment. Replaying the same invoice does not pay it twice.

### Outcome Measures

| Measure | Stage target |
|---|---:|
| INV-1001 end-to-end completion | 100% |
| Expected route | `APPROVE` |
| Mock payments after two identical submissions | Exactly 1 |
| Hard-failure variants reaching payment | 0 |
| Simulated reasoning repair cases completing one bounded cycle | 100% |
| Required graph-route and persistence tests | 100% passing |
| Clean-environment execution | Repeatable without manual data edits |

### Outcome Scope

- Process INV-1001 from local file intake through deterministic extraction, validation, approval, mock payment, and reconciliation.
- Show the canonical invoice, inventory checks, policy rules fired, terminal status, and payment result.
- Persist source identity, run state, events, and payment identity in SQLite.
- Reject one synthetic hard-failure variant and prove it cannot reach payment.
- Process one controlled ambiguous INV-1001 variant through structured simulated extraction, typed critic defects, one repair, and deterministic revalidation.
- Replay INV-1001 and return the recorded payment result without a second side effect.

### Verification Procedure

1. Start from an empty local database and run the setup command.
2. Submit `data/invoices/invoice_1001.txt` through the CLI.
3. Walk through the extracted vendor, amount, line items, evidence, inventory facts, and policy decision.
4. Show the successful mock payment and its idempotency key.
5. Submit the same invoice again and show that no second payment occurs.
6. Submit a negative-quantity variant and show deterministic rejection before payment.
7. Submit the ambiguous variant and show one bounded simulated-provider repair before the same deterministic controls run.

### Completion Evidence

- Structured CLI result for approval and rejection
- Persisted node timeline and rules fired
- Inventory records used by validation
- One payment ledger entry after two submissions
- Passing route tests proving hard failures cannot pay
- First candidate, typed critic defects, repaired candidate, and revalidation trace

### Implementation Work

- `pyproject.toml` with locked runtime and development dependencies
- `src/intellipay/` package and CLI entry point
- Configuration model for database path, reasoning mode, thresholds, retry limits, and feature flags
- Canonical typed models for invoices, line items, evidence, findings, decisions, payment commands, and workflow state
- Stable route, severity, finding, and payment-status codes
- Structured logging with run and document correlation
- Test fixtures and baseline lint, format, type-check, and pytest commands
- SQLite migrations and local database initialization
- Intake service that validates the path, limits size, hashes content, detects type, and records source metadata
- Deterministic parser registry with the TXT parser needed by INV-1001
- Canonical schema validation and field evidence for selected parser values
- Narrow `ReasoningProvider` protocol, explicit default `local` mode, deterministic simulated adapter, and one bounded extraction-repair cycle for a controlled ambiguous fixture
- Seeded SQLite inventory repository using the required case data
- Required-field, quantity, arithmetic, item-existence, and stock checks
- Minimal versioned approval policy for low-risk approval and hard-failure routing
- Payment command, unique idempotency key, mock adapter, and payment ledger
- LangGraph state machine connecting intake, extraction, validation, approval, payment, reconciliation, and terminal nodes
- Structured CLI result and persisted event trace
- Developer setup, run, and troubleshooting documentation

### Outcome Gate

- [x] INV-1001 reaches `APPROVE` and produces one successful mock payment.
- [x] Re-running the same accepted invoice returns or references the existing payment result without a second side effect.
- [x] A synthetic negative quantity reaches `REJECT` and cannot invoke payment.
- [x] A controlled ambiguous fixture completes one structured extraction and critic-repair cycle, then passes the same deterministic checks as parser output.
- [x] Graph-route tests prove validation precedes approval and authorization precedes payment.
- [x] Restarting after a committed node resumes without repeating that node's side effect.
- [x] The package installs from a clean environment, migrations are repeatable, and static and focused automated checks pass.
- [x] The complete verification procedure can be repeated without manual database edits or hidden setup.

**Gate status:** Passed on 2026-08-12. See the [Stage 1 verification record](stage-1-verification.md) for commands and measured evidence.

## Stage 2: Control Every Supplied Invoice Deterministically

### Measurable Outcome

Accounts payable can submit every supplied invoice format and receive an explicit, evidence-backed approve, reject, or escalate result. Known invalid, duplicate, unavailable, high-value, and unsupported cases are controlled consistently and cannot reach payment incorrectly.

### Outcome Measures

| Measure | Stage target |
|---|---:|
| Supplied invoices reaching a terminal or review state | 100% |
| Supported supplied formats with a deterministic adapter | 100% |
| Hard-control recall on approved seed labels | 100% |
| Expected route agreement on approved seed labels | 100% |
| Rejected or escalated cases reaching payment | 0 |
| Original and revised INV-1004 both producing payment | 0 occurrences |
| Batch failures reported without aborting remaining cases | 100% |

### Outcome Scope

- Process the complete supplied corpus in one evaluation run.
- Inspect at least one clean approval, deterministic rejection, inventory escalation, linked revision, and unsupported-currency escalation.
- Show expected and actual fields, findings, routes, and side effects per case.

### Verification Procedure

1. Run the corpus evaluation from a clean database.
2. Show the route distribution and quality-gate summary.
3. Open INV-1009 and show why invalid values prevent payment.
4. Open INV-1002 and show inventory and high-value findings.
5. Compare INV-1004 with its revision and show duplicate-payment prevention.
6. Open INV-1014 and show that EUR is preserved while unresolved policy escalates.

### Completion Evidence

- Machine-readable corpus report
- Finding and route agreement by case
- Hard-control recall result
- Payment ledger proving prohibited cases did not pay
- Linked revision records for INV-1004

### Implementation Work

- JSON, XML, CSV, TXT, and committed PDF-fixture extraction adapters
- Normalization for dates, currency, repeated CSV fields, OCR-like values, and line items
- Recalculation of line totals, subtotal, tax, shipping, and grand total with configured tolerance
- Aggregate inventory demand by normalized item identity across all lines, while preserving line-level evidence
- Stable findings for missing fields, negative values, unknown items, unavailable stock, quantity mismatch, arithmetic mismatch, unsupported currency, high value, near-threshold combined risk, invalid or inconsistent dates, duplicate, and revision ambiguity
- Document, business-identity, revision, and payment-duplicate logic
- Explicit `APPROVE`, `REJECT`, and `ESCALATE` routes with reason codes
- Durable review-task record for escalated cases, without the full review interface
- Versioned evaluation manifest, gold invoices, gold findings, gold routes, and expected side effects for all supplied cases
- Isolated fixture runs for parser scoring and declared operational sequences for duplicates, revisions, and conflicting same-identity documents
- Parameterized end-to-end corpus suite and machine-readable result output

### Outcome Verification

- Every supplied document parses or reaches an explicit supported escalation.
- INV-1009 hard-fails for negative or missing values and cannot pay.
- INV-1002 and INV-1005 produce inventory and high-value findings; INV-1002 also detects its due-date/terms inconsistency.
- INV-1007 produces aggregate inventory, high-value, non-ISO-date, and $110 arithmetic-mismatch findings.
- INV-1003, INV-1008, and INV-1016 cannot invent catalog mappings or reach payment.
- INV-1003 records its relative due date as unparseable; INV-1008 records a combined near-threshold risk signal.
- INV-1013 aggregates repeated items before inventory comparison and records its $50 arithmetic discrepancy.
- INV-1004 and its revision are linked and cannot both produce payment.
- Equivalent TXT/PDF variants run independently for extraction scoring; ordered same-identity sequences detect duplicates or conflicting versions without a second payment.
- INV-1014 preserves EUR and escalates when currency policy is unresolved.
- Gold asset schemas validate before the corpus test runs.

### Outcome Gate

All supplied invoices reach their approved gold route or a documented draft-label discrepancy. Hard-control recall is 100% on approved seed labels, payment invariants pass, and per-case failures are reported without stopping the batch.

## Stage 3: Resolve Ambiguous Invoices Without Weakening Controls

### Measurable Outcome

Accounts payable can submit an ambiguous or OCR-damaged invoice and see IntelliPay either repair the structured extraction within a bounded attempt or escalate it safely. Model availability, malformed output, or hostile document instructions never weaken deterministic controls.

### Outcome Measures

| Measure | Stage target |
|---|---:|
| Designated repair case producing typed critic defects | 100% |
| Repair attempts exceeding configured limit | 0 |
| Accepted repairs with unresolved required defects | 0 |
| Invalid model outputs entering accepted graph state | 0 |
| Prompt-injection cases changing route, policy, tools, or payment authority | 0 |
| Injected model outages reaching defined fallback or escalation | 100% |
| Default automated suite runnable without network access | 100% |

### Outcome Scope

- Process one ambiguous invoice through first-pass extraction, typed critique, bounded repair, deterministic revalidation, and final route.
- Process one unrepairable invoice and show escalation after the attempt limit.
- Repeat with model access disabled and show defined offline behavior.
- Run an invoice containing hostile instructions and show that tools and routing remain unchanged.

### Verification Procedure

1. Submit INV-1012 or another approved ambiguous fixture.
2. Show the first structured candidate and its source evidence.
3. Show critic defect codes and the bounded repair request.
4. Show deterministic checks on the repaired candidate and the final route.
5. Disable the live provider and rerun to verify safe fallback.
6. Run the prompt-injection fixture and show that protected boundaries remain intact.

### Completion Evidence

- Attempt-by-attempt structured extraction trace
- Critic defects before and after repair
- Configured attempt limit and actual attempt count
- Offline fallback trace
- Adversarial test results showing zero boundary violations

### Implementation Work

- Narrow `ReasoningProvider` protocol for structured extraction and bounded decision critique
- Deterministic fake provider for default tests and verification without network access
- Optional xAI Grok adapter with configurable endpoint, model, timeout, retries, and credentials
- Single `reasoning_mode` setting with default `local` and opt-in `live`, recorded in every run and trace
- Prompt templates that delimit invoice text as untrusted data
- Strict response schemas and model-output validation
- Extraction critic that emits machine-readable defects such as total mismatch, missing evidence, and invalid date
- One configured bounded repair loop followed by acceptance or escalation
- One-pass enhanced-review critique that may make a recommendation stricter but cannot weaken hard findings
- Recorded prompt, model, attempt, latency, token, and redacted request/response metadata
- Opt-in live-model contract and regression suite separated from offline CI

### Outcome Verification

- A fake-provider ambiguous case fails first-pass checks, receives typed defects, repairs successfully, and proceeds.
- An unresolved repair exhausts its attempt limit and reaches review.
- Invalid model JSON and schema output cannot enter accepted workflow state.
- Embedded instructions cannot change tools, policy, routes, or payment authorization.
- Grok timeout or absence follows the defined deterministic fallback or escalation route without data loss.
- The same graph safety tests pass with fake and live adapters.

### Outcome Gate

The self-correction and unavailable-model paths are executable and traced, no adversarial fixture alters a protected boundary, offline CI remains deterministic, and live-model use is optional.

## Stage 4: Enable Reviewers to Resolve Exceptions

### Measurable Outcome

An accounts-payable reviewer can understand why an invoice escalated, inspect the relevant evidence and policy, take an allowed action, and see the same workflow resume safely without consulting raw logs.

### Outcome Measures

| Measure | Stage target |
|---|---:|
| Representative escalated tasks completed by reviewers | 100% |
| Reviewer answers to the four evaluation questions | 100% correct |
| Review actions with recorded actor and rationale | 100% |
| Duplicate decisions from refresh or resubmission | 0 |
| Disallowed actions executable through the interface | 0 |
| Resumed runs repeating committed payment side effects | 0 |
| Blocking usability defects in the primary review flow | 0 |

Active handling time and reviewer confidence are recorded as baselines in this stage; improvement targets require observed customer data rather than invented assumptions.

### Outcome Scope

- Show an escalated case in a durable review queue.
- Explain extracted values, source evidence, findings, confidence, rules fired, and available actions.
- Record a reviewer action and resume the original run from its checkpoint.
- Show completed history and prove that refresh or repeated submission does not duplicate the action.

### Verification Procedure

1. Open an escalated invoice from the review queue.
2. Compare source evidence with normalized fields and findings.
3. Explain why each action is available or disabled.
4. Record an allowed action with rationale.
5. Follow the resumed run to its permitted terminal state.
6. Refresh and resubmit to show idempotent review and payment behavior.

### Completion Evidence

- Review queue and invoice detail states
- Source-to-field evidence and policy reasons
- Actor, timestamp, rationale, and disposition record
- Before-and-after graph timeline
- Usability task results and handling-time baseline

### Implementation Work

- LangGraph interrupt and authenticated review-decision contract
- Durable review queue with status, reason, priority, timestamps, and disposition
- FastAPI server-rendered review interface showing source content, canonical fields, evidence, confidence, findings, policy rules, revision history, and event timeline
- Responsive approval surface limited to queue, concise case summary, route reasons, findings, and constrained approve, reject, or request-correction actions
- Desktop evidence workspace for side-by-side source comparison, full event timeline, and revision-lineage inspection
- Clear approve, reject, and request-correction actions limited by policy
- Resume flow that records the human actor and continues from the checkpoint without repeating prior work
- Structured event coverage for node start/end, attempts, findings, routes, model calls, review, payment, and reconciliation
- Evaluation report generator for case outcomes, extraction accuracy, finding metrics, route distribution, latency, model use, and payment safety
- Redaction of secrets and unnecessary sensitive content from normal telemetry

### Outcome Verification

- An escalated invoice appears in the review queue with understandable reasons.
- A permitted review action resumes the same run and records actor and rationale.
- Disallowed actions are disabled and explained.
- Refreshing or resubmitting a review action does not duplicate the decision or payment.
- Reviewers can answer the four usability questions in the [evaluation approach](../analysis/evaluation-approach.md#human-evaluation) without inspecting logs.
- Empty, loading, error, escalated, and completed states render without overlapping or missing controls.

### Outcome Gate

The review workflow operates end to end, interrupt and resume tests pass, telemetry is sufficient to reconstruct each supplied case, and a short usability check identifies no blocking comprehension or action errors.

## Stage 5: Pass the Functional MVP Quality Gates

### Measurable Outcome

IntelliPay passes the complete functional MVP quality gates from a clean environment: the supplied corpus reaches expected states, quality and safety targets are met, and the core approval, rejection, agent-assisted, review, and replay-protection paths complete with no critical defect.

### Outcome Measures

| Measure | MVP target |
|---|---:|
| Supplied invoices reaching expected terminal or review state | 100% |
| Payment and graph safety invariant tests | 100% passing |
| Hard-control recall on approved seed labels | 100% |
| Required-field extraction accuracy overall | At least 95% |
| Prompt-injection boundary violations | 0 |
| Injected model and payment outages reaching defined safe state | 100% |
| Duplicate payments during replay and retry tests | 0 |
| Critical open defects | 0 |
| Clean-environment setup and acceptance run | 100% repeatable |

### Outcome Scope

- Run setup, migrations, the complete offline test suite, and corpus evaluation from a clean environment.
- Verify one routine approval, deterministic rejection, bounded model repair, human-reviewed escalation, and replay-protected payment.
- Inspect aggregate and per-case quality, safety, latency, and cost evidence.
- Review known limitations and unresolved business policy without permissive defaults.

### Verification Procedure

1. Start from the documented clean setup.
2. Run the complete automated acceptance suite.
3. Present the quality-gate report and drill into any non-critical limitation.
4. Execute the five representative workflows end to end.
5. Show failure-injection results for model outage and unknown payment result.
6. Confirm the immutable MVP version and documented deferred scope.

### Completion Evidence

- Clean-run command transcript
- Versioned evaluation and quality-gate report
- Full corpus outcome matrix
- Safety, adversarial, resilience, and replay results
- Performance, model-use, and cost summary
- Known limitations and unresolved-policy register

### Implementation Work

- Mutation fixtures for OCR swaps, removed fields, changed totals, duplicate submissions, currency changes, and prompt injection
- Fault injection for model errors, SQLite locks, process restart, payment timeout, and unknown payment result
- Reconciliation behavior that queries by idempotency identity and never resubmits blindly
- Performance and cost measurements for representative local batches
- Clean-clone setup, migration, run, review, evaluation, and troubleshooting instructions
- Versioned evaluation report with overall and segmented metrics plus per-case failures
- Security and privacy review of secrets, untrusted input, logs, model payloads, and local persistence
- Known limitations and unresolved business-policy decisions
- Functional MVP release tag or equivalent immutable version identifier

### Outcome Verification

- The complete offline suite passes from a clean environment.
- Every supplied invoice reaches its expected state with a complete trace.
- Payment and graph safety invariants pass at 100%.
- Hard-control recall is 100% on approved seed labels.
- Required-field accuracy reaches the approved prototype threshold.
- No prompt-injection case changes route, policy, tool permissions, or payment authorization.
- Every injected model and payment outage reaches its defined safe state.
- The full evidence and lineage workflow completes on desktop without blocking layout or interaction defects.
- The queue, summary, findings, and constrained approval actions complete on a representative mobile viewport without blocking layout or interaction defects.

### Outcome Gate

All Functional MVP Definition items and prototype quality gates pass, no critical defect remains open, setup is reproducible, and unresolved policy choices are explicit rather than encoded as permissive defaults.

## Cross-Stage Workstreams

### Testing and Evaluation

- Add focused tests with each behavior rather than deferring coverage to Stage 5.
- Keep the default suite deterministic and offline.
- Version gold labels independently from test implementation.
- Convert every defect into a minimal permanent regression fixture.

### Security and Privacy

- Treat file names, document content, parser output, and model output as untrusted from Stage 1.
- Keep secrets out of graph state, fixtures, logs, and evaluation reports.
- Parameterize SQL and restrict repositories and tools by responsibility.
- Redact routine telemetry before adding live-model use or a reviewer interface.

### Documentation and Decisions

- Update commands and behavior as each phase becomes executable.
- Keep architecture diagrams and ADRs aligned with implemented boundaries.
- Create or supersede an ADR when implementation requires a materially different architectural choice.
- Keep production concerns documented but outside the MVP unless required by a safety gate.

### Observability

- Establish run and document correlation in Stage 1.
- Add node duration, attempt, finding, and route events alongside each graph node.
- Add model and payment metadata only at their controlled boundaries.
- Prefer stable structured fields over prose-only logs.

## Dependencies and Decision Needs

| Needed by | Dependency or decision | Owner |
|---|---|---|
| Stage 1 | Confirm prototype policy that permits INV-1001 auto-approval | Finance or product owner |
| Stage 2 | Approve seed gold routes and inventory-shortage interpretation | Finance and inventory owner |
| Stage 2 | Define arithmetic and amount tolerances used by deterministic rules | Finance |
| Stage 3 | Provide optional xAI credentials and approve model data handling | Security and solution owner |
| Stage 4 | Define reviewer identity for the local prototype and allowed actions | Product and finance |
| Stage 5 | Approve critical fields and prototype accuracy thresholds | Finance and product owner |

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

## Delivery Descope Order

If time is constrained, reduce scope in this order while preserving the Stage 1 safe-payment outcome and all payment, graph, and hard-control invariants:

1. Defer live xAI execution and retain the contract-tested `local` simulated provider.
2. Reduce mobile support to the high-value approve/reject/request-correction action; keep detailed evidence inspection desktop-only.
3. Reduce review analytics and visual polish while retaining the durable queue, evidence, allowed actions, actor, rationale, and resume behavior.
4. Reduce mutation, performance, and cost-report breadth while retaining supplied-corpus acceptance, adversarial boundary tests, and failure tests for model and payment.
5. Defer nonessential format refinements only when each affected document still reaches an explicit safe escalation.

Never descope payment idempotency, deterministic hard controls, audit evidence, offline reproducibility, or the measured completion of one bounded reasoning-and-repair cycle.

## Related Documents

- [Business case analysis](../analysis/business-case-analysis.md)
- [Proposed solution](../analysis/proposed-solution.md)
- [Architecture](../analysis/architecture.md)
- [Evaluation approach and needs](../analysis/evaluation-approach.md)
- [Architecture decision records](../adr/0001-use-langgraph-state-machine.md)