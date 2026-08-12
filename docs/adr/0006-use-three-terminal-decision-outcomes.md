# ADR-0006: Use Three Terminal Decision Outcomes

- **Status:** proposed
- **Date:** 2026-08-12
- **Decision owners:** To be assigned

## Context and Problem Statement

The supplied invoices include clean cases, deterministic failures, and cases where inventory meaning, authority, currency, confidence, revisions, or suspicious signals require human judgment. A binary approve-or-reject decision would either reject potentially valid invoices or approve cases whose uncertainty has not been resolved.

## Decision Drivers

- Prevent uncertain or unsupported cases from being approved silently
- Distinguish invalid invoices from invoices needing investigation
- Enable straight-through processing for valid low-risk cases
- Provide explicit queues and reasons for human review
- Measure false approvals, false escalations, and exception causes separately

## Considered Options

1. **Approve, reject, or escalate:** Represent uncertainty as an explicit review route
2. **Approve or reject:** Force every automated decision into a terminal binary result
3. **Human decision for every invoice:** Automate extraction and checks but require manual disposition for all cases

## Decision Outcome

Chosen option: **Approve, reject, or escalate**

The policy engine produces `APPROVE`, `REJECT`, or `ESCALATE`. Hard failures reject or request correction, valid low-risk invoices may be approved within delegated limits, and uncertainty or enhanced-review conditions escalate to a durable human review queue. Approval alone does not authorize payment; payment gates remain separate.

### Consequences

- **Positive:** Uncertainty is visible and cannot be converted into a permissive guess.
- **Positive:** Routine invoices can proceed while exceptions receive focused human attention.
- **Negative:** Review operations need ownership, reason codes, priorities, and service levels.
- **Negative:** Conservative thresholds may initially create a high exception rate.
- **Follow-up:** Define delegated authority, escalation reason codes, review SLAs, and confidence thresholds with business owners.

## Pros and Cons of the Options

### Approve, Reject, or Escalate

- **Good:** Separates invalid cases from unresolved cases and supports risk-based automation.
- **Bad:** Requires durable review workflow and careful policy calibration.

### Approve or Reject

- **Good:** Produces a simple terminal contract and straightforward reporting.
- **Bad:** Misrepresents uncertainty and encourages either unsafe approval or excessive rejection.

### Human Decision for Every Invoice

- **Good:** Keeps disposition authority entirely with current reviewers during early operation.
- **Bad:** Preserves a major cycle-time bottleneck and limits the value of high-confidence automation.

## Confirmation

Scenario tests must verify approval for policy-permitted routine invoices, rejection for deterministic hard failures, and escalation for low confidence, unsupported data, suspicious signals, high-value review, and unresolved revisions. Reporting must distinguish all three outcomes and their reason codes.

## More Information

- [Business case: supplied invoice evidence](../analysis/business-case-analysis.md#evidence-from-the-supplied-invoices)
- [Proposed solution: approval policy](../analysis/proposed-solution.md#approval-policy)
- [ADR-0007: Isolate payment behind an idempotent port](0007-isolate-payment-behind-idempotent-port.md)
