---
name: evaluate-submission
description: 'Assess IntelliPay implementation and demo readiness against the case evaluation criteria: functionality, code quality, agentic sophistication, shipping mindset, presentation, above/beyond, and UI/UX. Use for rubric reviews, submission readiness, gap analysis, demo preparation, or prioritizing the next implementation work.'
argument-hint: 'Optionally name a criterion, feature, or milestone to assess'
user-invocable: true
disable-model-invocation: false
---

# Evaluate IntelliPay Submission Readiness

Assess repository evidence against the case rubric and update the living scorecard at [submission-readiness](../../../submission-readiness/README.md). Keep readiness assessment separate from solution documentation and runtime artifacts.

## Evidence Standard

Classify each criterion as:

- `Demonstrated`: repeatable executable evidence exists
- `Designed`: documentation describes the intended behavior, but execution is absent or incomplete
- `Missing`: neither sufficient design nor executable evidence exists

Never count an ADR, diagram, interface, planned test, or acceptance criterion as proof that behavior works. Prefer commands, passing tests, generated reports, traces, screenshots, and observed user flows.

## Workflow

1. Read the evaluation criteria in `context/README.md` and the current scorecard.
2. Inspect the relevant implementation, tests, analysis, and ADRs. Keep the review scoped to the requested criterion or milestone when one is provided.
3. Discover documented setup, test, lint, type-check, evaluation, and application commands. Run the narrowest relevant commands before drawing conclusions.
4. For UI/UX evidence, run the application and verify the primary workflow at desktop and mobile sizes when browser tools are available. Check loading, empty, error, review, and completed states.
5. Map evidence to all seven criteria. Record exact repository paths and commands so another evaluator can reproduce the result.
6. Update only `submission-readiness/README.md` when evidence has changed. Do not add grading commentary to solution analysis, ADRs, product documentation, or runtime output.
7. Identify at most three next actions, ordered by how many weak criteria they improve and whether they unblock the golden demo.

## Criterion Checks

### Functionality

- Run the CLI or application through ingestion, extraction, validation, approval, and mock payment.
- Verify approve, reject, and escalate routes.
- Verify all supplied invoice cases reach expected outcomes.

### Code Quality

- Run tests, lint, formatting, and type checks available in the repository.
- Inspect typed boundaries, deterministic rules, dependency injection, error handling, and structured logging.
- Treat missing tests for payment and route invariants as high severity.

### Agentic Sophistication

- Confirm a real or fake `ReasoningProvider` participates in the graph.
- Capture structured model output, tool boundaries, critic defects, bounded retry, and fallback behavior.
- Verify the model cannot weaken hard controls, select arbitrary tools, or authorize payment.

### Shipping Mindset

- Compare implemented scope with the scorecard's Must Ship and Defer lists.
- Flag production infrastructure or generalized abstractions that delay the golden demo.
- Reward explicit limitations and measured scope cuts.

### Presentation

- Verify the demo connects the business baseline to live behavior and measured outcomes.
- Check that diagrams and ADRs match the implementation.
- Require a concise setup path and honest limitations.

### Above/Beyond

- Prefer demonstrable differentiators tied to core risk: revision safety, replay, prompt-injection resistance, offline operation, and evidence-rich review.
- Do not reward speculative or unrelated feature breadth.

### UI/UX

- Verify users can understand extraction, evidence, findings, route reasons, and available actions without reading logs.
- Check accessibility, responsive layout, clear statuses, disabled-action explanations, and recovery from errors.

## Output Format

Report findings first, ordered by score impact. Then provide:

1. Updated criterion statuses with evidence
2. The three highest-leverage next actions
3. Commands and artifacts used for verification
4. Residual risks or unverified claims

Edit the scorecard when the repository's evidence state has materially changed. Do not inflate status to make the submission look complete.