# ADR-0008: Use a Server-Rendered Review Interface

- **Status:** accepted
- **Date:** 2026-08-12
- **Decision owners:** To be assigned

## Context and Problem Statement

Escalated invoices require a reviewer to understand evidence, findings, and policy constraints, record an accountable action, and resume the interrupted workflow. The prototype needs a usable interface without introducing a separate frontend deployment or requiring full evidence inspection on a small screen.

## Decision Drivers

- Keep the prototype within the Python application and local offline runtime
- Preserve server-side enforcement of allowed review actions
- Support evidence-dense desktop review and focused mobile approval
- Minimize frontend build, deployment, and state-synchronization complexity
- Provide accessible, testable routes that can evolve independently of LangGraph nodes

## Considered Options

1. **FastAPI with server-rendered HTML:** Serve review routes and responsive pages from the Python application
2. **Separate single-page application:** Build an independent JavaScript frontend against an API
3. **CLI-only review:** Resolve review tasks through terminal commands

## Decision Outcome

Chosen option: **FastAPI with server-rendered HTML**

Use FastAPI routes and server-rendered templates for the local review queue and case detail. Small locally served JavaScript enhancements are permitted, but core review actions must remain functional without a separate frontend service. The server validates every action against persisted workflow state and policy; disabled controls are not an authorization boundary.

Desktop supports side-by-side source evidence, canonical fields, the full event timeline, and revision lineage. Mobile supports the queue, a concise case summary, findings and route reasons, and constrained approve, reject, or request-correction actions. Detailed evidence inspection is deliberately desktop-only for the MVP.

Do not add a forwarded development port until the executable interface exists and its actual listen port is known.

### Consequences

- **Positive:** The review experience shares Python models, authorization rules, persistence, and deployment with the workflow service.
- **Positive:** The mobile scope targets approval delay without forcing dense evidence tools into a small viewport.
- **Negative:** Server-rendered interaction is less fluid than a purpose-built client application for complex future workflows.
- **Negative:** The application must implement CSRF protection, secure session handling, accessible forms, and responsive testing.
- **Follow-up:** Select the template and locally served asset approach during Stage 4 implementation, then document and forward the actual development port if required.

## Pros and Cons of the Options

### FastAPI with Server-Rendered HTML

- **Good:** Reuses the Python stack, has one local process, and keeps action validation close to workflow state.
- **Bad:** Rich client-side interactions require deliberate progressive enhancement.

### Separate Single-Page Application

- **Good:** Provides maximum flexibility for interactive evidence exploration.
- **Bad:** Adds a second toolchain, API surface, deployment unit, and client-state boundary before the prototype proves value.

### CLI-Only Review

- **Good:** Has the smallest implementation and deployment footprint.
- **Bad:** Does not provide the evidence comparison, discoverability, or mobile approval experience required for reviewer evaluation.

## Confirmation

Stage 4 interface tests must prove that allowed actions are enforced server-side, refresh or resubmission cannot duplicate a decision, and the original graph resumes from its checkpoint. Browser tests must verify the full evidence workflow on desktop and the queue, summary, findings, and constrained approval actions on a representative mobile viewport. The dev-container configuration must not forward an interface port before the server is implemented.

## More Information

- [Proposed solution](../analysis/proposed-solution.md)
- [Evaluation approach: human evaluation](../analysis/evaluation-approach.md#human-evaluation)
- [Functional MVP implementation plan: Stage 4](../planning/implementation-plan.md#stage-4-enable-reviewers-to-resolve-exceptions)
- [ADR-0001: Use a LangGraph state machine](0001-use-langgraph-state-machine.md)
- [ADR-0006: Use three terminal decision outcomes](0006-use-three-terminal-decision-outcomes.md)