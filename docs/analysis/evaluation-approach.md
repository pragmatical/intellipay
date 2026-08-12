# IntelliPay Evaluation Approach and Needs

## Purpose

This document defines how to determine whether IntelliPay is correct, safe, useful, resilient, and economically viable. It covers engineering verification, model evaluation, human-review quality, operational behavior, and business outcomes from prototype through shadow pilot.

Evaluation is part of the solution lifecycle. Every result must identify the document, expected labels, application version, parser version, schema version, policy version, prompt version, model version, inventory snapshot, and test mode that produced it.

## Evaluation Questions

The evaluation program must answer six questions:

1. **Extraction correctness:** Did the system preserve and normalize the invoice facts accurately?
2. **Control correctness:** Did deterministic checks find every labeled integrity, inventory, duplicate, revision, and policy issue?
3. **Decision safety:** Did the graph choose an allowed route without permitting model output to weaken hard controls or authorize payment?
4. **Resilience:** Does the workflow fail safely and resume correctly when parsers, Grok, SQLite, review, or payment dependencies fail?
5. **User effectiveness:** Can an accounts-payable reviewer understand the evidence, resolve an exception, and trust the recorded rationale?
6. **Business value:** Does the system reduce material errors, cycle time, and handling effort without increasing false approvals or duplicate payments?

## Evaluation Principles

- Evaluate structured facts, findings, routes, and side effects rather than prose similarity.
- Treat false approval and duplicate payment as higher-cost errors than false escalation.
- Keep deterministic and live-model suites separate so normal development remains reproducible and offline.
- Version gold labels and require domain review when business policy affects the expected outcome.
- Test safety invariants at graph boundaries, not only through individual functions.
- Preserve failed cases and regressions as permanent fixtures.
- Segment results by format, vendor, risk, amount band, parser, model, and failure mode; do not hide weak segments in one average.
- Use the supplied corpus for functional acceptance, not statistical claims about production accuracy.

## Required Evaluation Assets

The implementation should maintain these version-controlled assets:

| Asset | Required content | Purpose |
|---|---|---|
| Manifest | Unique case ID, business invoice identity, path, format, scenario tags, relationship type, sequence group, and split | Defines the evaluated population without encoding expected behavior in test code |
| Gold invoice | Canonical fields, line items, raw-to-normalized expectations, and tolerated alternatives | Scores extraction and normalization |
| Gold findings | Stable finding code, severity, affected field or item, and expected facts | Scores deterministic controls |
| Gold route | Expected `APPROVE`, `REJECT`, or `ESCALATE`, acceptable reason codes, and policy assumptions | Scores graph and policy behavior |
| Expected side effects | Whether review and payment may occur, expected idempotency identity, and replay behavior | Verifies safety boundaries |
| Mutation catalog | Reusable document changes such as removed vendor, digit swap, duplicate submission, and injected instruction | Expands coverage beyond hand-authored examples |
| Failure scenarios | Dependency fault, injection point, expected retry count, and final route | Makes resilience tests deterministic |

Each gold record needs a label status of `draft`, `domain-reviewed`, or `approved`, plus the reviewer and review date. A test may prove technical behavior against a draft label, but business release decisions require approved labels.

## Dataset Strategy

### Seed Acceptance Corpus

Use every supplied invoice as a functional acceptance case. Preserve the original and revised INV-1004 as linked records rather than independent invoices.

Run the corpus in two complementary modes:

1. **Isolated fixture evaluation:** Each file runs from a clean operational state under its unique case ID. This scores parser and control behavior without treating alternate representations as prior submissions.
2. **Operational sequence evaluation:** Related files run in a declared order against shared state. This scores exact duplicates, revisions, conflicting documents, payment idempotency, and supersession behavior.

The manifest must classify same-identity files explicitly:

- INV-1011 TXT and PDF are equivalent format variants.
- INV-1012 TXT and PDF are equivalent format variants.
- INV-1013 JSON and PDF share an invoice identity but contain conflicting facts; isolated runs score each parser, while the ordered sequence must escalate the second document as a conflicting version and must not create a second payment.
- INV-1004 and INV-1004 R1 are an explicit revision sequence requiring a supersession decision.

| Scenario | Seed cases | Primary assertion |
|---|---|---|
| Clean baseline | 1001, 1004, 1011, 1015 | Correct extraction with no false hard failure |
| Stock mismatch | 1002, 1005, 1007, 1013 | Expected aggregate inventory finding for every affected item |
| Unknown or unavailable item | 1003, 1008, 1016 | Unknown or unavailable finding and no payment |
| Invalid values | 1009 | Negative and missing-value hard failures |
| Format and OCR resilience | 1002, 1006, 1007, 1008, 1012, 1014 | Correct normalization or explicit escalation with source evidence |
| Revision and duplicate | 1004 and 1004 R1 | Linked versions and duplicate-payment prevention |
| Complex pricing | 1010, 1013 | Arithmetic reconciliation, including the INV-1013 $50 discrepancy, and policy exception where required |
| High value | 1002, 1003, 1005, 1007, 1013 | Enhanced-review policy fires |
| Foreign currency | 1014 | EUR is preserved and unsupported policy is not invented |

INV-1007 must additionally produce an arithmetic finding for its $110 total discrepancy and preserve evidence for its non-ISO date normalization. Inventory validation aggregates quantities by normalized item identity across all lines before comparing demand with the inventory snapshot.

### Development Variants

Generate controlled variants from seed documents to test one changed property at a time. Include OCR substitutions, whitespace and field-order changes, repeated CSV keys, missing required fields, altered totals, date ambiguity, unknown items, quantity boundaries, changed currency, duplicate content under a new filename, and prompt-injection text.

Development variants may be visible to implementers and used for regression tests. Every production bug should add the smallest fixture that would have detected it.

### Locked Holdout

Before tuning prompts, confidence thresholds, or policy rules for a pilot, create a locked holdout set that implementers do not inspect. It must be stratified across formats, vendors, amount bands, currencies, clean cases, and exception classes. Only an evaluation owner may release aggregate holdout results.

### Shadow-Pilot Dataset

Use a de-identified sample of historical invoices processed in parallel with the current workflow. Record the human decision, active handling time, queue time, corrections, and final payment disposition. Do not allow IntelliPay to initiate real payment during shadow evaluation.

## Test Layers

| Layer | What it proves | Minimum examples |
|---|---|---|
| Unit | Pure parsing, normalization, arithmetic, and policy rules are correct | Decimal totals, date parsing, repeated-key CSV, amount threshold |
| Contract | Adapters satisfy typed request, response, timeout, and error contracts | Reasoning provider, inventory repository, review store, payment port |
| Persistence | Constraints and transactions preserve workflow invariants | Migrations, foreign keys, unique idempotency key, restart recovery |
| Graph route | State transitions and tool permissions enforce policy | Hard failure cannot pay, low confidence reviews, interrupt/resume |
| End to end | A source document reaches its expected route and side effects | Parameterized run across the supplied corpus |
| Mutation | Controls detect realistic document corruption | Digit swap, missing vendor, changed total, duplicate submission |
| Adversarial | Untrusted content cannot redirect policy or tools | Embedded instructions to ignore rules, reveal secrets, or pay |
| Failure injection | Dependency failures produce bounded retry and safe final state | Grok unavailable, invalid schema, DB lock, payment timeout, restart |
| Performance | Runtime and resource use meet prototype and pilot budgets | Batch throughput, p50/p95 latency, model calls, token and cost totals |
| Usability | Reviewers can understand and resolve exceptions | Task completion, correction accuracy, active handling time, confidence |
| Shadow | System outcomes agree with approved operational decisions | Historical comparison and disagreement review |

## Deterministic and Model Evaluation

### Offline Deterministic Suite

The default `local` mode test suite must use a deterministic simulated `ReasoningProvider`. It must run without network access and produce stable extraction candidates, critic defects, repair responses, and critique responses. This suite is the required gate for normal development and continuous integration. Every result records `reasoning_mode=local`.

### Live Grok Suite

`live` mode evaluation is opt-in and must never be required for an offline build. Pin the prompt template, response schema, model identifier, and supported sampling settings. Record `reasoning_mode=live`, redacted request and response hashes, latency, token usage, estimated cost, schema failures, retries, and final structured output.

Run repeated samples for cases that depend on model interpretation. Report the distribution of outcomes and structured-field accuracy rather than selecting the best response. A prompt or model change cannot be promoted if it regresses a hard-control route, increases unsafe approvals, or reduces critical-field accuracy beyond an agreed tolerance.

### Self-Correction Evaluation

For every case intended to exercise repair:

1. Record the first extraction candidate.
2. Run deterministic schema, evidence, and arithmetic checks.
3. Record machine-readable critic defects.
4. Permit only the configured bounded repair attempts.
5. Re-run the same checks on the repaired candidate.
6. Assert acceptance only when all required defects are resolved; otherwise assert escalation.

Measure first-pass validity, repair success rate, defects introduced during repair, attempts per case, and escalation after exhausted retries. A repair may not overwrite raw evidence or weaken a finding.

## Metrics

### Extraction

- Exact and normalized match for every required field
- Line-item precision, recall, and F1 keyed by item and occurrence
- Numeric absolute error and arithmetic consistency
- Critical-field completeness
- Evidence coverage for accepted fields
- Accuracy by confidence bucket, format, parser, and model version

### Validation and Decision

- Finding precision, recall, and F1 by stable code
- Hard-control recall
- Outcome confusion matrix for approve, reject, and escalate
- False approval and false escalation rates
- Reviewer agreement and override rate
- Straight-through processing rate segmented by risk and format

### Safety and Resilience

- Payment idempotency violations and duplicate attempts prevented
- Prompt-injection attempts that change route, policy, or tool permissions
- Retry count and final state by injected failure
- Restart and interrupt/resume success rate
- Unknown payment results reconciled without blind resubmission
- Offline completion and escalation rates

### Operational and Cost

- End-to-end and per-node p50/p95 latency
- Model calls, tokens, estimated cost, timeout rate, and schema-repair rate
- Human active handling time, queue age, and rework count
- Throughput and resource use for representative batches

### Business

- Material error rate compared with the 30% baseline
- Intake-to-decision cycle time compared with the five-day baseline
- Labor minutes and rework avoided
- Late fees avoided and early-payment discounts captured
- Invalid or duplicate payment leakage prevented
- Gross benefit, operating cost, and net annualized benefit with a confidence range

## Quality Gates

### Prototype Acceptance

- Every supplied invoice reaches an expected terminal or human-review state with a complete trace.
- Labeled negative values, unknown items, unavailable items, and duplicates achieve 100% hard-control recall.
- Payment and graph safety invariant tests pass with no exceptions.
- Replaying an approved invoice cannot produce a second payment.
- No adversarial document can alter route, policy, tool permissions, or payment authorization.
- Every injected model and payment outage reaches its defined safe state.
- Required-field extraction accuracy is at least 95% overall, with critical-field thresholds approved by the domain owner.

### Model or Prompt Promotion

- Structured-output contract tests pass.
- No hard-control or payment-safety regression occurs in offline or live suites.
- Critical-field and route metrics remain within approved regression tolerances.
- Repeated live samples show acceptable variance for model-dependent cases.
- Latency and estimated cost remain within the configured budget.
- Data handling and redaction checks pass for the selected provider configuration.

### Shadow-Pilot Exit

- Finance approves the gold labels, outcome confusion matrix, and false-approval threshold.
- Treasury approves payment command, idempotency, and reconciliation evidence while real payment remains disabled.
- Routine-case cycle time and active handling time improve against the measured baseline.
- Reviewer disagreement and overrides are categorized and resolved into policy, data, UX, or model changes.
- No unresolved critical security, privacy, or audit finding remains.

Production authorization requires separate decisions for delegated authority, acceptable false-approval rate, data retention, availability, recovery, and real treasury integration.

## Human Evaluation

Accounts-payable reviewers should complete representative tasks without consulting raw logs. Sessions must include a clean invoice, inventory mismatch, ambiguous extraction, revision, and high-value case.

Measure task completion, correction accuracy, active handling time, requests for help, incorrect actions, and confidence in the outcome. Capture whether reviewers can answer:

1. What did IntelliPay extract?
2. Which source evidence supports each material value?
3. Which findings and policy rules caused the route?
4. What action is available, and what will happen after it is selected?

Usability findings must become tracked product changes or explicitly accepted limitations.

## Instrumentation and Tooling Needs

The solution needs:

- A deterministic evaluation runner that accepts a manifest and produces machine-readable per-case results
- Versioned gold-label loaders with schema validation
- Test fixtures for fake reasoning, inventory snapshots, review decisions, and payment responses
- Fault-injection controls for model, database, checkpoint, and payment boundaries
- Structured events with run, document, node, attempt, duration, route, finding, policy, parser, prompt, and model metadata
- A report generator for extraction metrics, finding metrics, confusion matrices, safety gates, latency, cost, and case-level failures
- A secure opt-in live-model test configuration that never exposes credentials in fixtures or reports
- Reproducible random seeds and recorded versions for generated mutations
- CI jobs for offline tests and a separately authorized workflow for live-model evaluation

## Ownership and Review Cadence

| Owner | Evaluation responsibility |
|---|---|
| Engineering | Test harness, deterministic labels, graph invariants, failures, performance, and reproducibility |
| Accounts payable | Field expectations, correction workflow, reason clarity, and reviewer usability |
| Finance or delegated approver | Outcome labels, approval policy, tolerances, and false-approval threshold |
| Procurement or inventory owner | Inventory semantics, item identity, shortage interpretation, and data freshness |
| Treasury | Payment authorization, idempotency, unknown-result handling, and reconciliation |
| Security and privacy | Adversarial tests, secrets, data minimization, provider terms, access, and retention |
| Product owner | Business baseline, benefit measurement, scope, and release decision |

Run the offline suite on every change. Run mutation and failure suites before merging changes to graph, policy, persistence, or payment behavior. Run the live-model suite only for prompt, schema, adapter, or model changes. Review aggregate quality and operational metrics at each prototype increment and at a regular cadence during shadow pilot.

## Evaluation Report

Each evaluation run should produce:

- Configuration and component versions
- Dataset identity and label status
- Overall and segmented metrics
- Quality-gate pass or fail results
- Per-case expected and actual fields, findings, route, and side effects
- Model attempts and critic defects where applicable
- Latency, token, and cost summaries
- New failures and regressions compared with the approved baseline
- Links to redacted traces sufficient to reproduce each failure

Reports must not include secrets or unnecessary raw financial and personal data. A passing summary without per-case failure detail is insufficient for diagnosis or release review.

## Open Evaluation Decisions

The following require named owners before shadow-pilot exit:

1. Critical fields and minimum per-field accuracy thresholds
2. Acceptable false-approval and false-escalation rates
3. Approved interpretation of inventory availability
4. Amount, quantity, price, tax, and total tolerances
5. Review service levels and maximum queue age
6. Model latency and cost budgets
7. Minimum holdout size and sampling strategy
8. Data retention and de-identification rules for evaluation artifacts
9. Production performance, availability, recovery, and reconciliation objectives

## Related Solution Documents

- [Business case analysis](business-case-analysis.md)
- [Proposed solution](proposed-solution.md)
- [Architecture](architecture.md)
- [ADR-0002: Use deterministic-first invoice processing](../adr/0002-use-deterministic-first-processing.md)
- [ADR-0003: Isolate Grok behind a reasoning provider](../adr/0003-isolate-grok-behind-reasoning-provider.md)
- [ADR-0007: Isolate payment behind an idempotent port](../adr/0007-isolate-payment-behind-idempotent-port.md)