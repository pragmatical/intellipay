# ADR-0001: Use a LangGraph State Machine for Invoice Processing

- **Status:** accepted
- **Date:** 2026-08-12
- **Decision owners:** To be assigned

## Context and Problem Statement

Invoice processing must coordinate extraction, validation, approval, human review, payment, and reconciliation. The workflow must survive retries and process restarts, pause for human decisions, prevent invalid transitions, and preserve enough state to reproduce each outcome. A free-form collaboration among autonomous agents would make those controls difficult to enforce and audit.

## Decision Drivers

- Explicit and testable routing between processing stages
- Durable checkpoints and resumable human review
- Enforcement of payment and approval invariants
- Reproducible outcomes and bounded retries
- Agentic behavior without unconstrained tool access

## Considered Options

1. **LangGraph state machine:** Typed state, explicit nodes and transitions, checkpoints, and interrupts
2. **Free-form agent collaboration:** Autonomous agents coordinate through messages and choose their own transitions
3. **Custom procedural workflow:** Hand-written orchestration and persistence without a workflow framework

## Decision Outcome

Chosen option: **LangGraph state machine**

Use LangGraph to orchestrate a typed invoice workflow. Each node receives limited tools, emits durable serializable state, and follows explicit transition policy. This directly supports retries, checkpoints, human interrupts, and routing invariants while retaining bounded model-assisted behavior.

### Consequences

- **Positive:** Workflow routes, retries, and terminal outcomes can be tested independently of model behavior.
- **Positive:** Interrupted runs can resume without repeating committed work or payment side effects.
- **Negative:** State schemas, node boundaries, and transition rules require more design and maintenance up front.
- **Follow-up:** Define the typed graph state, checkpoint boundaries, interrupt payloads, and invariant tests.

## Pros and Cons of the Options

### LangGraph State Machine

- **Good:** Provides explicit state transitions, checkpointing, and human-in-the-loop primitives.
- **Bad:** Introduces a framework dependency and requires disciplined state modeling.

### Free-Form Agent Collaboration

- **Good:** Flexible for open-ended tasks and rapid experimentation.
- **Bad:** Makes routing, authorization, reproducibility, and failure recovery harder to guarantee.

### Custom Procedural Workflow

- **Good:** Minimizes framework-specific concepts and gives full implementation control.
- **Bad:** Requires custom checkpoint, resume, interrupt, and state-transition infrastructure.

## Confirmation

Automated graph tests must prove that hard failures cannot reach payment, low-confidence fields route to retry or review, interrupted runs resume from committed checkpoints, and resumed runs do not repeat payment side effects.

## More Information

- [Proposed solution: LangGraph workflow](../analysis/proposed-solution.md#langgraph-workflow)
- [Architecture: workflow architecture](../architecture/architecture.md#workflow-architecture)
- [ADR-0007: Isolate payment behind an idempotent port](0007-isolate-payment-behind-idempotent-port.md)
