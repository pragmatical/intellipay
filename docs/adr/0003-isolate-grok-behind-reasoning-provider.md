# ADR-0003: Isolate Grok Behind a Reasoning Provider

- **Status:** accepted
- **Date:** 2026-08-12
- **Decision owners:** To be assigned

## Context and Problem Statement

The proposed solution uses xAI Grok for ambiguous extraction and bounded approval critique. Tests and offline runs must not require network access, model configuration will change independently of workflow code, and model responses are an untrusted boundary. Coupling graph nodes directly to the xAI API would spread provider details and make deterministic testing difficult.

## Decision Drivers

- Offline and deterministic test execution
- Centralized model configuration, retries, and data handling
- Replaceability as model APIs and approved providers evolve
- Narrow model capabilities with no direct payment or policy authority
- Structured outputs that can be validated at one boundary

## Considered Options

1. **ReasoningProvider interface:** Expose only invoice extraction and decision critique operations
2. **Direct xAI calls in graph nodes:** Let each model-using node construct and execute API requests
3. **Provider-neutral chat abstraction:** Expose a general chat-completion interface to workflow nodes

## Decision Outcome

Chosen option: **ReasoningProvider interface**

Place xAI behind a narrow application-owned interface with structured `extract_invoice` and `critique_decision` operations. Provide an xAI adapter for configured runs and a deterministic fake for tests and offline development. Keep endpoint, model, credentials, timeout, retry, and retention settings outside workflow code.

Expose two explicit modes through one configuration setting. `local` is the default and uses deterministic simulated reasoning with no external API access. `live` is opt-in and calls xAI with configured credentials. Both modes implement the same contract, preserve all deterministic controls, and record the selected mode in run metadata.

### Consequences

- **Positive:** Workflow and policy tests can run without network access or model variance.
- **Positive:** Provider-specific concerns and untrusted-output validation have a clear boundary.
- **Negative:** The interface may expose only the lowest common capabilities needed by the workflow.
- **Negative:** Provider-specific features require deliberate adapter or interface evolution.
- **Follow-up:** Define typed request and result contracts, fake-provider fixtures, redaction rules, and opt-in live-model tests.

## Pros and Cons of the Options

### ReasoningProvider Interface

- **Good:** Matches domain operations and prevents arbitrary model-controlled tool use.
- **Bad:** Requires maintaining adapters and versioning the domain contract.

### Direct xAI Calls in Graph Nodes

- **Good:** Provides immediate access to all xAI features with little initial abstraction.
- **Bad:** Couples orchestration to one API and duplicates configuration, retries, and validation.

### Provider-Neutral Chat Abstraction

- **Good:** Makes generic model replacement straightforward.
- **Bad:** Exposes a broader capability than the workflow needs and pushes prompt and schema discipline into each caller.

## Confirmation

The same graph tests must pass with the deterministic fake and xAI adapter contract tests. Static dependency checks or code review must confirm that graph nodes depend on `ReasoningProvider`, not an xAI client, and that model output cannot directly alter policy, human decisions, routing invariants, or payment authorization.

## More Information

- [Proposed solution: xAI Grok integration](../analysis/proposed-solution.md#xai-grok-integration)
- [Architecture: reasoning architecture](../architecture/architecture.md#reasoning-architecture)
- [ADR-0002: Use deterministic-first invoice processing](0002-use-deterministic-first-processing.md)
