# Finance and Domain Label Approval Runbook

**Purpose:** Convert the 20 Stage 2 draft invoice labels into reviewed business-policy evidence without conflating software behavior with finance approval.  
**Primary artifact:** [Stage 2 manifest](../../evaluation/stage2-manifest.json)  
**Supporting evidence:** [Stage 2 report](../../evaluation/stage2-report.json) and [verification record](../planning/stage-2-verification.md)

## Completion Standard

This workstream is complete when:

- Every manifest case has been reviewed against the original source and applicable policy.
- Every case has a final `approved` label or a documented unresolved policy decision.
- Reviewer identity, authority, review date, rationale, and disagreements are recorded.
- The corpus evaluator matches all approved labels or every discrepancy is explicitly accepted.
- Finance or its delegated approver signs the final approval record.

Engineering test success does not constitute domain approval.

## Roles

| Role | Responsibility |
|---|---|
| Finance approver | Owns final outcome, payment expectation, tolerance, and policy decisions |
| Accounts-payable reviewer | Confirms field meaning, exception handling, and operational route |
| Inventory or procurement reviewer | Confirms item identity, stock interpretation, and revision semantics when relevant |
| Engineering facilitator | Prepares evidence, demonstrates deterministic behavior, records decisions, and applies approved changes |
| Independent reviewer | Resolves disputed high-risk labels when the primary reviewers disagree |

One named person may hold multiple roles, but the final finance approver must have delegated authority to approve the labels.

## Inputs

- All files under [data/invoices](../../data/invoices/)
- [Stage 2 manifest](../../evaluation/stage2-manifest.json)
- [Stage 2 report](../../evaluation/stage2-report.json)
- Current inventory fixture and validation policy
- Relevant finance policies for dates, currency, amount thresholds, duplicates, revisions, and payment eligibility
- A copy of the approval record template at the end of this runbook

## Preparation

1. Name the finance approver, AP reviewer, facilitator, and any specialist reviewers.
2. Confirm the policy version or policy documents used during review.
3. Run the current baseline:

   ```bash
   uv sync --all-groups
   uv run intellipay-evaluate --output evaluation/stage2-report.json
   uv run pytest -q
   ```

4. Confirm the report contains 20 cases, zero batch errors, and zero prohibited payments before beginning business review.
5. Prepare a review packet for each case containing:
   - Original invoice source
   - Canonical invoice fields and line items
   - Expected outcome and findings from the manifest
   - Actual outcome and findings from the report
   - Expected and actual payment behavior
   - Applicable policy or inventory evidence
6. Review linked files together:
   - INV-1004 original and revision
   - INV-1011 TXT and PDF variants
   - INV-1012 TXT and PDF variants
   - INV-1013 JSON and PDF variants

## Per-Case Review Procedure

For each of the 20 cases:

1. Open the original source. Do not begin from the expected label.
2. Confirm the invoice identity, vendor, dates, currency, totals, terms, and line items.
3. Compare the canonical extraction to the source and classify any difference:
   - `IMPLEMENTATION_DEFECT`: parser or normalization is wrong.
   - `FIXTURE_DEFECT`: source data is malformed or unsuitable for its intended scenario.
   - `POLICY_GAP`: expected treatment is not defined by approved policy.
   - `LABEL_DEFECT`: implementation is correct but the draft expected label is wrong.
   - `NO_DEFECT`: extraction and draft interpretation are acceptable.
4. Review every expected finding. Confirm that it is factually supported and policy-relevant.
5. Select exactly one expected terminal outcome:
   - `APPROVE`: valid and eligible for automated payment controls.
   - `REJECT`: deterministically invalid or unsafe.
   - `ESCALATE`: requires authorized human judgment or unresolved policy.
6. Confirm `payment_expected` independently from the outcome label. An approval recommendation alone does not bypass payment authorization controls.
7. Record the decision, rationale, reviewer, and policy reference in the approval record.
8. Mark disagreements for resolution. Do not average reviewer opinions or silently choose the implementation's current output.

## Disagreement Resolution

1. The facilitator records both positions and the disputed fact or policy.
2. Implementation defects go to engineering and retain `draft` status until fixed and rerun.
3. Label defects are corrected only after finance approval.
4. Policy gaps go to the policy owner; the safest interim route remains `ESCALATE`.
5. High-risk disputes involving payment eligibility require the finance approver's explicit decision.
6. Record the final decision and why the rejected alternative was not selected.

## Applying Approved Changes

1. Update only the approved fields in [evaluation/stage2-manifest.json](../../evaluation/stage2-manifest.json).
2. Set a case's `label_status` to `approved` only after its review is complete.
3. Do not add reviewer or date keys to the manifest without first updating the typed `EvaluationCase` schema. The current schema rejects extra fields.
4. Keep reviewer, date, authority, policy reference, rationale, and disagreement history in the approval record below or in a dated copy of it.
5. Regenerate evidence:

   ```bash
   uv run intellipay-evaluate --output evaluation/stage2-report.json
   uv run pytest -q
   uv run ruff check .
   uv run ruff format --check src tests
   ```

6. Investigate every approved-label discrepancy. Do not change an approved label merely to make a test pass.

## Final Gate

The finance approver verifies:

- [ ] All 20 cases were reviewed from source evidence.
- [ ] All approved labels have an outcome, findings, and payment expectation.
- [ ] Linked revisions and format variants were reviewed as sequences where applicable.
- [ ] Policy gaps and accepted limitations are documented.
- [ ] No prohibited payment occurred in the final report.
- [ ] The final evaluator has zero unexplained discrepancies against approved labels.
- [ ] The approval record is signed and dated.

## Approval Record Template

Create a dated copy of this section for the actual review. One row is required per manifest case.

**Review date:**  
**Policy version or references:**  
**Finance approver:**  
**AP reviewer:**  
**Engineering facilitator:**  

| Case ID | Final outcome | Final findings | Payment expected | Status | Reviewer | Rationale or policy reference |
|---|---|---|---:|---|---|---|
| inv-1001-txt |  |  |  | draft |  |  |
| inv-1002-txt |  |  |  | draft |  |  |
| inv-1003-txt |  |  |  | draft |  |  |
| inv-1004-json |  |  |  | draft |  |  |
| inv-1004-r1-json |  |  |  | draft |  |  |
| inv-1005-json |  |  |  | draft |  |  |
| inv-1006-csv |  |  |  | draft |  |  |
| inv-1007-csv |  |  |  | draft |  |  |
| inv-1008-txt |  |  |  | draft |  |  |
| inv-1009-json |  |  |  | draft |  |  |
| inv-1010-txt |  |  |  | draft |  |  |
| inv-1011-pdf |  |  |  | draft |  |  |
| inv-1011-txt |  |  |  | draft |  |  |
| inv-1012-pdf |  |  |  | draft |  |  |
| inv-1012-txt |  |  |  | draft |  |  |
| inv-1013-json |  |  |  | draft |  |  |
| inv-1013-pdf |  |  |  | draft |  |  |
| inv-1014-xml |  |  |  | draft |  |  |
| inv-1015-csv |  |  |  | draft |  |  |
| inv-1016-json |  |  |  | draft |  |  |

### Disagreement Log

| Case ID | Positions | Classification | Owner | Resolution | Date |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### Sign-Off

**Finance decision:** Approved / Approved with limitations / Not approved  
**Approved limitations:**  
**Finance approver name:**  
**Authority or role:**  
**Approval date:**  
**Signature or recorded approval reference:**  
