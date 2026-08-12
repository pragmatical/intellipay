# Finance and Domain Label Review Simulation

- **Exercise status:** Complete
- **Date:** 2026-08-12
- **Review type:** Tabletop simulation with automated corpus evidence
- **Authority:** Simulated finance approver and AP reviewer
**Manifest status applied:** `simulated-reviewed`

## Goal

Rehearse the full label-approval procedure, verify that every expected route and finding is internally consistent with the supplied invoice corpus, and expose gaps before requesting an authorized finance sign-off.

## Value

The simulation proves that the review packet, decision vocabulary, linked-document handling, evaluator, and evidence format are usable end to end. It also creates a precise baseline for an authorized reviewer, reducing the future session to business judgment rather than process discovery.

## Method

1. Treated the manifest as a draft hypothesis, not as proof.
2. Reviewed each fixture through the deterministic extraction, validation, routing, and payment result.
3. Compared expected and actual route, findings, and payment behavior.
4. Reviewed revision and equivalent-format cases as linked groups.
5. Classified discrepancies using the runbook categories.
6. Re-ran the isolated corpus after applying the simulation status.

## Results

| Measure | Result |
|---|---:|
| Cases reviewed | 20/20 |
| Route agreements | 20/20 |
| Finding agreements | 20/20 |
| Payment agreements | 20/20 |
| Hard-control cases recalled | 4/4 |
| Prohibited payments | 0 |
| Batch errors | 0 |
| Disagreements | 0 |

## Case Record

| Case | Simulated decision | Findings | Payment | Rationale |
|---|---|---|---:|---|
| inv-1001-txt | APPROVE | None | Yes | Complete supported invoice with no control finding |
| inv-1002-txt | ESCALATE | HIGH_VALUE; INSUFFICIENT_STOCK; PAYMENT_TERMS_DATE_MISMATCH | No | Human review required and stock blocks approval |
| inv-1003-txt | ESCALATE | HIGH_VALUE; INVALID_DATE; UNKNOWN_ITEM | No | Invalid date and unknown item require resolution |
| inv-1004-json | APPROVE | None | Yes | Valid original in a revision sequence |
| inv-1004-r1-json | APPROVE | None | Yes | Valid revision is handled as the authoritative sequence member |
| inv-1005-json | ESCALATE | HIGH_VALUE; INSUFFICIENT_STOCK | No | Enhanced review required and stock blocks payment |
| inv-1006-csv | APPROVE | None | Yes | Complete supported invoice with no control finding |
| inv-1007-csv | REJECT | HIGH_VALUE; INSUFFICIENT_STOCK; TOTAL_MISMATCH | No | Arithmetic failure is a hard rejection control |
| inv-1008-txt | ESCALATE | NEAR_THRESHOLD_RISK; UNKNOWN_ITEM | No | Ambiguous item and threshold risk require judgment |
| inv-1009-json | REJECT | INVALID_QUANTITY; MISSING_REQUIRED_FIELD; SUBTOTAL_MISMATCH; TOTAL_MISMATCH | No | Malformed quantities and arithmetic failures are unsafe |
| inv-1010-txt | APPROVE | None | Yes | Complete supported invoice with no control finding |
| inv-1011-pdf | APPROVE | None | Yes | PDF representation agrees with its equivalent source |
| inv-1011-txt | APPROVE | None | Yes | Text representation agrees with its equivalent source |
| inv-1012-pdf | APPROVE | None | Yes | OCR result agrees with its equivalent source |
| inv-1012-txt | APPROVE | None | Yes | Text representation confirms the OCR result |
| inv-1013-json | REJECT | HIGH_VALUE; INSUFFICIENT_STOCK; TOTAL_MISMATCH | No | Arithmetic failure is a hard rejection control |
| inv-1013-pdf | REJECT | HIGH_VALUE; INSUFFICIENT_STOCK; TOTAL_MISMATCH | No | Equivalent PDF preserves the same hard-control result |
| inv-1014-xml | ESCALATE | UNSUPPORTED_CURRENCY | No | Currency requires unsupported-policy review |
| inv-1015-csv | APPROVE | None | Yes | Complete supported invoice with no control finding |
| inv-1016-json | ESCALATE | UNKNOWN_ITEM | No | Item identity requires human resolution |

## Linked-Case Review

- INV-1004: original and revision were treated as one business sequence, not unrelated invoices.
- INV-1011 and INV-1012: PDF and text forms produced equivalent business treatment.
- INV-1013: JSON and PDF forms preserved the same rejection findings without a false version conflict.

## Disagreements and Limitations

No internal discrepancy was found between the labels and measured behavior. This is evidence of consistency, not independent policy correctness: the simulated roles had no delegated finance authority, and no production policy document was supplied for formal citation.

## Simulation Decision

- **Decision:** Simulation passed
- **Labels:** Marked `simulated-reviewed`
- **Exercise closure:** Complete
**External authorization:** Not claimed
