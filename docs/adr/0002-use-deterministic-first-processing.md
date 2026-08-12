# ADR-0002: Use Deterministic-First Invoice Processing

- **Status:** accepted
- **Date:** 2026-08-12
- **Decision owners:** To be assigned

## Context and Problem Statement

The invoice corpus contains known JSON, XML, CSV, TXT, and PDF formats as well as malformed and ambiguous content. Financial arithmetic, required fields, duplicate detection, inventory checks, and approval limits must be predictable and cannot depend on model opinion. Model reasoning remains useful for noisy extraction and bounded critique where deterministic methods are insufficient.

## Decision Drivers

- Predictable enforcement of financial and policy controls
- Offline processing for known formats
- Lower model cost and latency for routine invoices
- Safe handling of ambiguity without silent guessing
- Measurable extraction and validation behavior

## Considered Options

1. **Deterministic-first processing:** Parse and validate with code first; invoke Grok only for ambiguity and bounded critique
2. **LLM-first processing:** Send every invoice through a model for extraction and decision support
3. **Deterministic-only processing:** Build format-specific parsers and rules without model assistance

## Decision Outcome

Chosen option: **Deterministic-first processing**

Known formats use deterministic parsers, schema validation, arithmetic, and policy rules. Grok is invoked only when extraction is incomplete or ambiguous, or when policy calls for bounded critique. Model output must pass the same schema and deterministic controls before entering accepted graph state.

### Consequences

- **Positive:** Routine invoices remain processable when the model or network is unavailable.
- **Positive:** Hard controls are reproducible and cannot be weakened by model output.
- **Negative:** Multiple parser adapters and their fixtures must be maintained.
- **Negative:** New document layouts may initially have a higher review rate.
- **Follow-up:** Implement parser selection, confidence thresholds, bounded model retries, and deterministic validation tests.

## Pros and Cons of the Options

### Deterministic-First Processing

- **Good:** Balances predictable controls with model-assisted handling of noisy documents.
- **Bad:** Requires orchestration between parsers, model extraction, confidence checks, and review.

### LLM-First Processing

- **Good:** Offers one flexible extraction path across heterogeneous formats.
- **Bad:** Increases cost, availability dependency, variance, and exposure to hallucination and prompt injection.

### Deterministic-Only Processing

- **Good:** Maximizes repeatability and supports fully offline execution.
- **Bad:** Handles OCR damage and novel unstructured layouts poorly and expands adapter maintenance.

## Confirmation

The evaluation suite must show that known-format fixtures complete without a live model, all model outputs receive schema and arithmetic validation, hard-control outcomes are identical with fake and live reasoning providers, and ambiguous unresolved fields route to review.

## More Information

- [Proposed solution: design principles](../analysis/proposed-solution.md#design-principles)
- [Proposed solution: deterministic controls](../analysis/proposed-solution.md#deterministic-controls)
- [ADR-0003: Isolate Grok behind a reasoning provider](0003-isolate-grok-behind-reasoning-provider.md)
