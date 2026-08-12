# ADR-0005: Preserve Evidence-Level Lineage

- **Status:** accepted
- **Date:** 2026-08-12
- **Decision owners:** To be assigned

## Context and Problem Statement

Invoices may be malformed, revised, normalized from OCR, or interpreted by a model. Reviewers and auditors need to understand where each accepted field came from, which transformations occurred, which parser or model produced it, and which policy and reference snapshots informed the outcome. Storing only the final normalized invoice would make disputed decisions and regressions difficult to reconstruct.

## Decision Drivers

- Reproducible extraction, validation, approval, and payment decisions
- Reviewer access to source spans, confidence, and transformations
- Safe handling of revisions and reprocessing without rewriting history
- Evaluation by parser, model, schema, and policy version
- Auditability without placing raw sensitive content in routine telemetry

## Considered Options

1. **Evidence-level lineage:** Preserve immutable source identity, field evidence, versions, findings, decisions, and event references
2. **Final-record persistence:** Keep the accepted canonical invoice and terminal outcome only
3. **Raw logs and model transcripts:** Reconstruct lineage primarily from unstructured execution logs

## Decision Outcome

Chosen option: **Evidence-level lineage**

Store immutable source hashes and references, candidate and accepted invoice versions, field-level evidence, normalization details, confidence, producer versions, validation findings, reference snapshots, policy versions, decisions, and append-only event references. Corrections and reprocessing create new linked versions rather than mutating historical records.

For the prototype, implement the smallest useful form of this decision: retain the source document and hash, one canonical invoice version, field evidence produced by the selected parser or model, validation findings, the policy version and rules fired, the terminal decision, and the payment result. Defer generalized version graphs, coordinate-level evidence for every format, retention automation, and tamper-evident event chaining until after the end-to-end workflow and evaluation harness pass.

### Consequences

- **Positive:** Review, dispute resolution, regression evaluation, and audit reconstruction use structured evidence.
- **Positive:** Revisions and replay runs remain distinguishable from the original decision and payment.
- **Negative:** Storage, schema, privacy controls, and retention management become more complex.
- **Negative:** Every parser and model adapter must produce consistent evidence metadata.
- **Follow-up:** Define the prototype evidence contract first, then add generalized lineage, redaction, access, and retention controls as measured needs emerge.

## Pros and Cons of the Options

### Evidence-Level Lineage

- **Good:** Connects every accepted fact and decision to its source and producer version.
- **Bad:** Adds relational entities, storage volume, and governance obligations.

### Final-Record Persistence

- **Good:** Keeps storage and application queries simple.
- **Bad:** Cannot explain normalization, model interpretation, changed decisions, or revision history reliably.

### Raw Logs and Model Transcripts

- **Good:** Capture detailed execution context with little initial schema design.
- **Bad:** Are difficult to query, may expose sensitive data, and do not enforce stable lineage relationships.

## Confirmation

For every evaluated invoice, the prototype must trace each accepted field to source evidence and a parser or model version, each finding to the inventory snapshot, and each outcome to policy metadata. Replay tests must not mutate the prior decision or enable payment side effects. Production-grade lineage remains unconfirmed until generalized versioning and governance controls are implemented.

## More Information

- [Proposed solution: canonical invoice contract](../analysis/proposed-solution.md#canonical-invoice-contract)
- [Architecture: canonical data layers](../analysis/architecture.md#canonical-data-layers)
- [Architecture: replay and reprocessing](../analysis/architecture.md#replay-and-reprocessing)
