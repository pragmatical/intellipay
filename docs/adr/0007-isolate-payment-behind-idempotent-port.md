# ADR-0007: Isolate Payment Behind an Idempotent Port

- **Status:** accepted
- **Date:** 2026-08-12
- **Decision owners:** To be assigned

## Context and Problem Statement

Payment is the highest-impact side effect in the invoice workflow. Duplicate submissions, retries after unknown results, model tool access, or coupling approval directly to the banking API could cause financial loss. The prototype must demonstrate the complete control flow without moving real money and must preserve a narrow boundary for a future treasury integration.

## Decision Drivers

- Prevention of duplicate payment across retries, revisions, and replay
- Separation of recommendation, authorization, execution, and reconciliation
- Least-privileged access to payment capability
- Safe simulation in prototype and shadow-pilot environments
- Replaceable integration with future treasury controls

## Considered Options

1. **Separate idempotent payment port:** Submit an authorized payment command through a narrow adapter and ledger
2. **Direct banking API call from approval workflow:** Let the approval node invoke payment after returning approval
3. **No payment boundary in the prototype:** Stop at approval and defer payment design until production integration

## Decision Outcome

Chosen option: **Separate idempotent payment port**

Create a payment command only after policy and authority gates pass. Send that command to a narrow adapter with a unique idempotency key, record its result in a payment ledger, and reconcile unknown outcomes before any retry. Use only a mock adapter in the prototype; Grok and general workflow nodes receive no payment tool access.

### Consequences

- **Positive:** Payment invariants can be tested end to end without real money movement.
- **Positive:** Retries, process restarts, revisions, and replay cannot legitimately create duplicate commands.
- **Negative:** Command, ledger, reconciliation, and unknown-result states add workflow complexity.
- **Negative:** A production adapter still requires treasury-specific authorization and dual-control design.
- **Follow-up:** Define the idempotency-key derivation, signed authorization contract, reconciliation states, and adapter contract tests.

## Pros and Cons of the Options

### Separate Idempotent Payment Port

- **Good:** Contains the financial side effect behind an auditable, replaceable, and least-privileged boundary.
- **Bad:** Requires additional state, persistence, error handling, and reconciliation logic.

### Direct Banking API Call from Approval Workflow

- **Good:** Has a shorter implementation path from approval to payment.
- **Bad:** Couples decision and execution, broadens privileges, and makes retries and unknown outcomes dangerous.

### No Payment Boundary in the Prototype

- **Good:** Eliminates payment-side-effect risk during early development.
- **Bad:** Defers validation of idempotency and reconciliation, which are central acceptance risks for the solution.

## Confirmation

Contract and graph tests must prove that payment requires an authorized command, duplicate idempotency keys return the recorded result without resubmission, unknown outcomes enter reconciliation, hard failures and escalations cannot reach the adapter, and replay mode disables payment.

## More Information

- [Proposed solution: LangGraph workflow](../analysis/proposed-solution.md#langgraph-workflow)
- [Architecture: payment trust boundary](../analysis/architecture.md#runtime-and-trust-boundaries)
- [Business case: risks and mitigations](../analysis/business-case-analysis.md#risks-and-mitigations)
- [ADR-0001: Use a LangGraph state machine](0001-use-langgraph-state-machine.md)