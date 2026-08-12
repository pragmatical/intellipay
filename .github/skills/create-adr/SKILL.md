---
name: create-adr
description: 'Create, draft, update, or supersede Architecture Decision Records (ADRs) in docs/adr. Use when documenting an architecture decision, technical choice, trade-off, rejected option, or decision consequence.'
argument-hint: 'Describe the architecture decision to record'
user-invocable: true
disable-model-invocation: false
---

# Create Architecture Decision Records

Create concise, evidence-based ADRs using the repository's MADR-style template.

## Workflow

1. Read relevant repository documentation and implementation before drafting. Identify the decision, its scope, constraints, stakeholders, and already-established facts.
2. Inspect `docs/adr/` for existing records. Reuse established conventions when they differ from this skill.
3. Determine whether the request needs a new ADR, an update to a draft ADR, or a superseding ADR:
   - Update an existing ADR only while its status is `proposed` and the decision has not materially changed.
   - Preserve accepted, rejected, deprecated, and superseded ADRs as historical records.
   - Create a new ADR for a materially different decision and link both records when one supersedes another.
4. For a new ADR, choose the next unused four-digit sequence number. Use the filename `docs/adr/NNNN-short-kebab-case-title.md`.
5. Copy [the ADR template](./assets/adr-template.md) and replace every placeholder. Use the current date in `YYYY-MM-DD` format.
6. Present options fairly. Explain why the chosen option best satisfies the decision drivers and record meaningful disadvantages, risks, and follow-up work.
7. Validate the completed ADR against the checklist below.

## Writing Rules

- Record one architectural decision per ADR.
- State the decision directly and use active voice.
- Derive context and constraints from repository evidence; do not invent facts or consensus.
- Ask the user only for information that cannot be established from the repository and materially changes the decision.
- Keep implementation detail only when it explains an architectural constraint or consequence.
- Include at least two considered options unless the ADR documents a forced choice; explain the constraint when no viable alternative exists.
- Use repository-relative Markdown links for related ADRs and documents.
- Keep unresolved matters in `More Information`; do not disguise them as decided.
- Do not delete historical ADRs or renumber existing records.

## Status Values

Use exactly one lowercase status:

- `proposed`: under discussion and not yet approved
- `accepted`: approved for implementation
- `rejected`: considered and explicitly declined
- `deprecated`: no longer recommended, without a direct replacement
- `superseded`: replaced by a newer ADR, which must be linked

Default new ADRs to `proposed` unless repository evidence or the user confirms another status.

## Validation Checklist

- The filename has the next available sequence number and a descriptive slug.
- No template placeholders remain.
- The status and date are valid.
- Context explains the problem without assuming the outcome.
- Decision drivers are specific enough to compare options.
- The outcome identifies one chosen option and explains why.
- Positive and negative consequences are both recorded.
- Confirmation describes how the decision's adoption will be verified.
- Related ADR and documentation links resolve.
- Supersession links are reciprocal when applicable.
