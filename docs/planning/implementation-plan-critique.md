# Solution, ADR, and Implementation Plan Critique

## Purpose

This document records a review of the [proposed solution](../analysis/proposed-solution.md), the [architecture decision records](../adr/0001-use-langgraph-state-machine.md), and the [functional MVP implementation plan](implementation-plan.md) against the problem and requirements stated in the [case brief](../../context/README.md).

All recommendations were reviewed against the case brief, current architecture, supplied fixtures, and delivery constraints. Each recommendation was accepted with the scope recorded below and has been applied to the linked artifacts.

Review date: 2026-08-12
Decision date: 2026-08-12

## Overall Assessment

The core approach is sound and no redesign is recommended. Deterministic-first control with a narrow model boundary, three explicit outcomes, evidence lineage, and payment isolated behind an idempotent port is an appropriate architecture for an accounts-payable control system. The ADRs record genuine trade-offs, and the staged plan with measurable outcome gates is a strong delivery structure.

The findings below concentrate on two areas: requirement risk against the case brief, and gold-label correctness where verified invoice data conflicts with documented expectations.

## Recommendation Summary

| # | Recommendation | Priority | Primary artifact | Decision |
|---|---|---|---|---|
| 1 | Make live and local reasoning modes an explicit, tested contract | High | ADR-0003, plan | Accepted |
| 2 | Move a minimal agentic path earlier than Stage 3 | High | Implementation plan | Accepted |
| 3 | Reconcile the decision-outcome vocabulary | High | Proposed solution, ADR-0006 | Accepted |
| 4 | Define line-item aggregation semantics | High | Proposed solution, plan | Accepted |
| 5 | Resolve the duplicate versus format-variant collision | High | Plan, evaluation approach | Accepted |
| 6 | Correct the documented expectation for INV-1007 | High | Proposed solution, plan | Accepted |
| 7 | Add a near-threshold approval signal | Medium | Proposed solution | Accepted |
| 8 | Add explicit date-integrity findings | Medium | Proposed solution | Accepted |
| 9 | Record a review-interface decision as an ADR | Medium | ADR set | Accepted |
| 10 | Fix stale generated-PDF wording | Low | Implementation plan | Accepted |
| 11 | Add an explicit descope order | Low | Implementation plan | Accepted |
| 12 | Scope mobile review to the approval action | Low | Implementation plan | Accepted |
| 13 | Accept the ADRs being built on | Low | ADR set | Accepted |

## Implementation Record

| # | Accepted scope and applied change |
|---|---|
| 1 | Added explicit default `local` and opt-in `live` modes to [ADR-0003](../adr/0003-isolate-grok-behind-reasoning-provider.md), the [proposed solution](../analysis/proposed-solution.md), evaluation, and plan. Local mode simulates external APIs; it does not require a local model server. |
| 2 | Added one controlled structured extraction and critic-repair cycle to Stage 1; Stage 3 retains full ambiguous-corpus, adversarial, failure, and optional live-provider hardening. |
| 3 | Retained `APPROVE`, `REJECT`, and `ESCALATE` as the only workflow outcomes; `HOLD` is an escalation reason and `REQUEST_CORRECTION` is a follow-up action. Updated [ADR-0006](../adr/0006-use-three-terminal-decision-outcomes.md). |
| 4 | Defined inventory demand as aggregate quantity by normalized item identity and made INV-1013 the discriminating case in the solution, evaluation approach, and plan. |
| 5 | Split evaluation into isolated fixture runs and ordered operational sequences. Equivalent variants score extraction independently; conflicting same-identity documents exercise escalation and payment idempotency. |
| 6 | Added INV-1007's $110 arithmetic discrepancy and non-ISO date normalization to the solution, evaluation approach, and Stage 2 verification. |
| 7 | Added a configurable near-threshold combined risk signal. It requires another risk factor such as unknown vendor or item and is not an automatic fraud verdict. |
| 8 | Added explicit findings for unparseable or relative dates and due dates inconsistent with stated payment terms. |
| 9 | Added [ADR-0008](../adr/0008-use-server-rendered-review-interface.md), selecting a FastAPI server-rendered interface and deferring port forwarding until the executable server exists. |
| 10 | Replaced generated-PDF wording with committed PDF-fixture wording. |
| 11 | Added a delivery descope order that protects payment safety, hard controls, evidence, offline operation, and one bounded reasoning loop. |
| 12 | Limited mobile scope to queue, summary, findings, and constrained approval actions; detailed evidence and lineage remain desktop-only. |
| 13 | Changed ADR-0001 through ADR-0007 to `accepted`; ADR-0008 is also accepted. Decision owners remain to be assigned rather than inferred. |

## High Priority: Requirement Risk

### 1. Make live and local reasoning modes an explicit, tested contract

**Observation.** The case brief requires xAI Grok as the reasoning engine and states that the runtime should assume no internet access for external APIs, simulating them locally. The intent is that external services are stubbed, not that a local model server is required. [ADR-0003](../adr/0003-isolate-grok-behind-reasoning-provider.md) already establishes the correct boundary: a narrow `ReasoningProvider` with a live xAI adapter and a deterministic simulated adapter.

**Risk.** The mode is currently implied rather than specified. Without a named, configurable switch and tests covering both paths, verification can silently depend on network availability, or the simulated path can drift from the live contract.

**Recommendation.** Define two explicit operating modes and make them a first-class part of the contract.

- **Local mode:** the default. All external services, including Grok and payment, are simulated locally, and the full workflow runs without network access.
- **Live mode:** opt-in through configuration and credentials, calling the real xAI API while all other controls remain unchanged.

Record the mode in run output and traces, select it through a single documented setting, and require the same graph and safety tests to pass in both modes. This clarifies the existing decision rather than introducing a new dependency.

### 2. Move a minimal agentic path earlier than Stage 3

**Observation.** Stages 1 and 2 of the [implementation plan](implementation-plan.md) are entirely deterministic. No model participation, tool use, or self-correction exists until Stage 3 of 5.

**Risk.** The case objective is a multi-agent system with function calling, structured outputs, and self-correction loops. If delivery is interrupted, the result is a deterministic invoice validator with no agentic behavior.

**Recommendation.** Move one structured model extraction and one critic repair cycle into Stage 1 or Stage 2 so the agentic spine exists early, even if it initially covers a single ambiguous invoice.

### 3. Reconcile the decision-outcome vocabulary

**Observation.** [ADR-0006](../adr/0006-use-three-terminal-decision-outcomes.md) and the implementation plan define exactly three outcomes: `APPROVE`, `REJECT`, and `ESCALATE`. The [approval policy](../analysis/proposed-solution.md#approval-policy) additionally uses `REQUEST_CORRECTION` and `HOLD`.

**Risk.** Gold routes, policy tests, reviewer actions, and reporting all encode this vocabulary. Two competing models will produce inconsistent labels and ambiguous test expectations.

**Recommendation.** Choose one model. Either express correction and hold as reason codes within the three outcomes, or expand the enum deliberately and update ADR-0006, the plan, and the evaluation assets together.

## High Priority: Gold-Label Correctness

### 4. Define line-item aggregation semantics

**Observation.** [invoice_1013.json](../../data/invoices/invoice_1013.json) contains eight line items with repeated products. Evaluated per line, every quantity is within stock. Evaluated as an aggregate per item, all three products breach the seeded inventory.

| Item | Line quantities | Aggregate | Seeded stock | Per-line result | Aggregate result |
|---|---|---:|---:|---|---|
| WidgetA | 15, 5, 2 | 22 | 15 | Passes | Breach |
| WidgetB | 10, 8 | 18 | 10 | Passes | Breach |
| GadgetX | 5, 3, 1 | 9 | 5 | Passes | Breach |

**Risk.** The expected route for INV-1013 depends entirely on an unstated rule. Gold labels cannot be approved until it is decided.

**Recommendation.** State explicitly that inventory checks aggregate quantity by item across all line items, and record INV-1013 as the discriminating fixture for that rule.

### 5. Resolve the duplicate versus format-variant collision

**Observation.** The corpus contains 20 files representing 16 invoice identities plus one revision. Three identities exist as two files each.

| Invoice | Files | Content relationship |
|---|---|---|
| INV-1011 | `invoice_1011.txt`, `invoice_1011.pdf` | Same invoice, two formats |
| INV-1012 | `invoice_1012.txt`, `invoice_1012.pdf` | Same invoice, two formats |
| INV-1013 | `invoice_1013.json`, `invoice_1013.pdf` | Same invoice number, **different line items and totals** |

**Risk.** A full-corpus run will raise duplicate findings for the same invoice number, and INV-1013 presents two conflicting documents for one identity. Both effects will distort route agreement and duplicate-payment metrics.

**Recommendation.** Decide and document whether each pair is processed as a duplicate submission, an independent format variant in a separate run scope, or a conflicting-version case requiring supersession. Reflect the decision in the evaluation manifest so the corpus run is interpretable.

### 6. Correct the documented expectation for INV-1007

**Observation.** The proposed solution and plan describe INV-1007 as an inventory mismatch and high-value case only. [invoice_1007.csv](../../data/invoices/invoice_1007.csv) also contains an arithmetic error.

- Line totals: 5,000.00 + 7,500.00 + 2,250.00 = 14,750.00, matching the stated subtotal.
- Stated tax at 6%: 885.00, which is arithmetically correct.
- Expected total: 14,750.00 + 885.00 = 15,635.00.
- Stated total: 15,525.00, a discrepancy of 110.00.

The file also uses `01/28/2026` while most fixtures use ISO dates, exercising ambiguous date parsing.

**Recommendation.** Add the arithmetic-mismatch finding and the date-format variance to the documented expectations for INV-1007 before gold labels are written.

## Medium Priority

### 7. Add a near-threshold approval signal

**Observation.** [invoice_1008.txt](../../data/invoices/invoice_1008.txt) totals 9,900.00 against the stated 10,000.00 enhanced-review threshold, arrives as an email body from an unknown vendor, and contains two items absent from inventory.

**Recommendation.** Add a deterministic signal for amounts falling just below an approval threshold, combined with unknown vendor or unknown item. This is a recognized threshold-evasion pattern and is currently captured only as an unknown-item finding.

### 8. Add explicit date-integrity findings

**Observation.** Current extraction controls specify required fields and valid ISO dates. Two fixtures fail in ways that are not explicitly covered.

- [invoice_1003.txt](../../data/invoices/invoice_1003.txt) has `Due Date: yesterday`, which is unparseable and accompanies urgency and wire-transfer language.
- [invoice_1002.txt](../../data/invoices/invoice_1002.txt) has a due date equal to its invoice date while stating Net 30 terms.

**Recommendation.** Define findings for unparseable or relative dates and for due dates inconsistent with stated payment terms.

### 9. Record a review-interface decision as an ADR

**Observation.** UI/UX is an explicit evaluation criterion, but no ADR records the review-interface technology, its boundary, or how it is served. Stage 4 refers only to a "lightweight review interface".

**Recommendation.** Add an ADR selecting the review-interface approach, its scope, and what it deliberately excludes. Add any required port forwarding to the dev container at that point rather than in advance.

## Low Priority

### 10. Fix stale generated-PDF wording

Stage 2 lists "generated PDF extraction adapters". The generation utility has been removed and the PDFs are now committed fixtures. Update the wording to avoid implying a regeneration step.

### 11. Add an explicit descope order

The plan defines what is outside the MVP but does not state what is cut first if delivery time is constrained. An explicit reduction order protects the measurable outcome.

### 12. Scope mobile review to the approval action

**Observation.** Stage 5 verification requires that desktop and mobile review workflows complete without blocking layout or interaction defects. Mobile appears only in that one verification line, with no decision recording why it is in scope. The Stage 4 interface is dense comparison work: source content beside canonical fields, evidence, confidence, findings, policy rules, revision history, and an event timeline.

**Business justification for keeping mobile.** The [business case](../analysis/business-case-analysis.md#root-causes) identifies email-based approval as a root cause producing lost context and serial waiting, and attributes part of the five-day cycle to it. The high-value approver is the person most often away from a desk, so a mobile-capable approval action targets the cycle-time metric directly. Removing mobile entirely would discard that benefit.

**Recommendation.** Split the requirement by task rather than making the entire interface responsive.

- **Mobile supported:** the review queue, a case summary with route reasons and findings, and the approve, reject, and request-correction actions with their policy constraints.
- **Desktop only:** side-by-side source-to-field evidence comparison, the full event timeline, and revision-lineage inspection.

Update the Stage 5 verification line to match this split so the gate exercises the approval path on mobile without requiring the full evidence view to be responsive.

### 13. Accept the ADRs being built on

All seven ADRs remain `proposed` with owners "To be assigned", while the implementation plan treats them as settled. Accepting the decisions that work is proceeding on would reflect their actual status.

## Related Documents

- [Case brief](../../context/README.md)
- [Proposed solution](../analysis/proposed-solution.md)
- [Evaluation approach and needs](../analysis/evaluation-approach.md)
- [Functional MVP implementation plan](implementation-plan.md)
- [Architecture decision records](../adr/0001-use-langgraph-state-machine.md)
