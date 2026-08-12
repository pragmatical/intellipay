# Accounts-Payable Usability Simulation

- **Exercise status:** Complete
- **Date:** 2026-08-12
- **Review type:** Scripted tabletop exercise with one live browser walkthrough
**Participants:** Three simulated AP personas; no human participant claims

## Goal

Rehearse the usability protocol across representative invoice exceptions and verify that the interface and evidence model can answer the four questions an AP reviewer needs before taking action.

## Value

The simulation checks scenario coverage, moderator wording, expected answers, action constraints, and evidence capture before using AP staff time. It is especially valuable for finding protocol gaps and obvious interface blockers, while remaining separate from evidence about real comprehension, confidence, or handling speed.

## Simulation Design

Three tabletop personas were applied consistently:

| Persona | Working profile |
|---|---|
| AP-SIM-01 | Experienced exception handler focused on policy and auditability |
| AP-SIM-02 | Regular invoice processor focused on source-to-field verification |
| AP-SIM-03 | New IntelliPay user focused on navigation and action consequences |

The live browser walkthrough used INV-1002. Remaining scenarios were evaluated from the supplied corpus and the same interface contract. Synthetic personas were not assigned handling times or confidence scores because those measures require real participants.

## Scenario Results

| Scenario | Fixture | Extracted facts and evidence | Route explanation | Available action and consequence | Result |
|---|---|---|---|---|---|
| Clean invoice | INV-1001 | Source supports canonical vendor, dates, items, and total | No findings; normal payment controls apply | No exception action required | PASS |
| Inventory mismatch | INV-1002 | GadgetX quantity 20 and USD 15,000 are visible beside source text | High value, insufficient stock, and terms/date mismatch cause review | Reject or request correction; approval is disabled and no payment occurs | PASS |
| Ambiguous extraction | INV-1008 | Source item is retained with an unknown-item finding | Near-threshold risk and unknown item require judgment | Resolve through human review; no payment before resolution | PASS |
| Revision or duplicate | INV-1004 | Original and revised documents share one business identity | Sequence metadata prevents treating versions as unrelated invoices | Authoritative revision proceeds through controls without duplicate payment | PASS |
| High value | INV-1005 | Canonical total and line quantity are traceable to source | High value and insufficient stock require review | Approval remains blocked by stock; reject or request correction | PASS |
| Prohibited approval | INV-1013 | Source and canonical arithmetic expose total mismatch | Hard arithmetic control plus stock finding causes rejection | Approval cannot be executed; payment remains blocked | PASS |

## Live Walkthrough Evidence

The INV-1002 page exposed, without raw logs:

- Original invoice text and a direct source link.
- Normalized vendor, invoice number, dates, terms, total, and line item.
- Three named findings with human-readable explanations.
- The policy route and run timeline.
- A required rationale field.
- Disabled `APPROVE` with an explanation that a non-overridable control remains.
- Available `REJECT` and `REQUEST CORRECTION` actions with stated consequences.

All four required evaluation questions could be answered from the interface for this case.

## Control Evidence

| Control | Evidence | Result |
|---|---|---|
| Authentication | Review routes require configured reviewer credentials | PASS |
| Action authorization | Server validates task-bound allowed actions | PASS |
| Rationale | Decision requires non-empty rationale | PASS |
| Replay safety | Identical decision replay is idempotent | PASS |
| Conflicting replay | A different completed decision is rejected | PASS |
| Duplicate side effects | Repeated completion creates one decision event and no duplicate payment | PASS |

## Findings

| Finding | Severity | Disposition |
|---|---|---|
| Disposable demo contains only one live review case | Minor | Keep tabletop fixtures for rehearsal; seed all scenarios before human sessions |
| Real handling time is not available from simulation | Expected limitation | Measure with AP participants |
| Real confidence and help-request rates are not available from simulation | Expected limitation | Measure with AP participants |

No blocking protocol, navigation, comprehension-model, or action-control defect was found in the simulation.

## Simulation Decision

- **Decision:** Simulation passed with expected limitations
- **Scenario coverage:** 6/6
- **Scripted four-question checks:** 24/24 answerable
- **Prohibited actions executable:** 0
- **Duplicate decisions or payments:** 0
- **Exercise closure:** Complete
**Representative human usability validation:** Not claimed
