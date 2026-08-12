# Business Case Analysis: Invoice Processing Automation

## Executive Summary

Acme Corp is losing approximately **$2 million per year** through a manual invoice process with a **30% error rate** and an average **five-day cycle time**. The current workflow combines unstructured email and document intake, manual data entry, checks against an inconsistent legacy inventory source, VP approval through email, and payment through a banking API. This creates avoidable labor cost, late-payment risk, duplicate-payment risk, weak controls, and poor auditability.

The proposed business direction is a controlled invoice automation service that normalizes incoming documents, applies deterministic financial and inventory controls, uses an LLM only where interpretation is necessary, routes uncertain or high-risk cases to people, and makes payment an idempotent, auditable action. The initial goal is not touchless processing for every invoice. It is high-confidence automation for routine cases and faster, better-supported review for exceptions.

The supplied dataset supports this approach. It includes clean invoices as well as OCR corruption, malformed CSV, email-body invoices, stock shortages, unknown and zero-stock items, a negative invoice, duplicate revisions, pricing anomalies, foreign currency, suspicious urgency, and invoices above the $10,000 review threshold. A successful prototype must demonstrate correct handling of these cases rather than optimize only for clean extraction.

## Business Problem

### Current-State Workflow

1. Invoices arrive through email, primarily as PDFs and other inconsistent attachments.
2. Staff manually extract vendor, amount, items, quantities, and due date.
3. Staff perform validation by comparing invoice content with a legacy inventory database.
4. VP approval is requested through email chains, especially for higher-value invoices.
5. Approved invoices are submitted to a banking API for payment.
6. Errors and rejections are handled manually with limited structured evidence.

### Root Causes

| Root cause | Operational effect | Business consequence |
|---|---|---|
| Heterogeneous and noisy documents | Re-keying and interpretation effort | High labor cost and extraction errors |
| Incomplete or inconsistent reference data | Manual investigation and inconsistent decisions | False approvals, false rejections, and delays |
| Email-based approvals | Lost context, serial waiting, weak escalation | Five-day processing cycle and frustrated stakeholders |
| Unstructured decision rationale | Difficult audit and dispute resolution | Compliance and control exposure |
| No reliable duplicate or revision control | Same obligation can be represented more than once | Duplicate-payment and overpayment risk |
| Payment coupled to human judgment without system gates | Inconsistent execution controls | Fraud and erroneous-payment exposure |

## Evidence From the Supplied Invoices

The test corpus represents several distinct business risks:

| Risk class | Examples | Required response |
|---|---|---|
| Clean, routine invoices | INV-1001, INV-1004, INV-1011, INV-1015 | Process with high-confidence controls |
| Stock mismatch | INV-1002, INV-1005, INV-1007 | Block payment and route for reconciliation |
| Unknown or unavailable item | INV-1003, INV-1008, INV-1016 | Block or escalate; never infer inventory validity |
| Invalid financial data | INV-1009 | Reject negative quantities/totals and missing required fields |
| Suspicious behavior | INV-1003 | Escalate or reject based on combined fraud indicators |
| Duplicate or revision | INV-1004 and INV-1004 R1 | Preserve both versions; prevent duplicate payment |
| OCR or format degradation | INV-1002, INV-1006, INV-1012 | Recover where confidence is sufficient; otherwise request review |
| Pricing complexity | INV-1010, INV-1013 | Reconcile totals and compare with PO/contract when available |
| Foreign currency | INV-1014 | Require currency-aware policy and approved FX source |
| High value | INV-1002, INV-1003, INV-1005, INV-1007, INV-1013 | Apply the stated $10,000 enhanced-review policy |

This evidence argues against a single LLM prompt that decides whether to pay. Extraction, policy checks, approval, and payment need separate controls and audit records.

## Target Business Outcomes

### Primary Outcomes

| Outcome | Baseline | Proposed target | Measurement |
|---|---:|---:|---|
| Processing error rate | 30% | Below 5% | Material errors / invoices processed |
| End-to-end cycle time | 5 days | Below 1 business day for routine invoices | Intake-to-decision timestamp |
| Annual avoidable cost | $2M | Validate through pilot; recover a material share | Labor, rework, late fees, and prevented leakage |
| Inventory mismatch detection | Not stated | 100% on labeled test cases | Correct mismatch flags / known mismatches |
| Invalid-data detection | Not stated | 100% for negative totals, negative quantities, and missing required fields | Correct hard-control outcomes |
| Duplicate payment | Not stated | Zero | Duplicate payments executed |

### Guardrail Metrics

- **Straight-through processing rate:** percentage paid without human intervention. This should rise only after accuracy targets are met.
- **Exception rate:** percentage escalated for review, segmented by cause and vendor.
- **False approval rate:** invalid or fraudulent invoices approved. This is more important than maximizing automation.
- **False escalation rate:** valid invoices unnecessarily sent to reviewers.
- **Extraction accuracy:** exact-match accuracy by field, line item, and format.
- **Reviewer handling time:** active minutes spent on an exception, excluding queue time.
- **Payment idempotency failures:** repeated payment attempts or duplicate settlement records.
- **LLM availability, latency, and cost:** measured separately from deterministic pipeline performance.

## Value Hypothesis

The stated $2M annual loss is a business baseline, not yet a validated benefit forecast. A defensible benefits model should separate:

1. **Labor capacity:** invoices per month multiplied by current handling minutes, loaded labor rate, and automatable share.
2. **Rework reduction:** error volume multiplied by average correction cost.
3. **Working-capital and fee effects:** late fees avoided and early-payment discounts captured.
4. **Leakage prevented:** duplicate, invalid, or suspicious payments blocked.
5. **Technology and operating cost:** implementation, model usage, support, reviewers, and control maintenance.

The pilot should establish these inputs before claiming the full $2M as realized savings. Benefits should be reported as gross savings, operating cost, and net savings, with a range rather than a single-point estimate.

## Proposed Scope

### MVP In Scope

- Local ingestion of PDF, TXT, JSON, CSV, XML, and email-body content.
- Canonical extraction of invoice identity, vendor, dates, currency, totals, and line items.
- Arithmetic, required-field, date, quantity, inventory, duplicate, and revision checks.
- Rule-based approval with enhanced scrutiny above $10,000.
- Grok-assisted extraction and bounded critique for ambiguous cases.
- Explicit `APPROVE`, `REJECT`, and `ESCALATE` outcomes.
- Mock payment with idempotency protection.
- Structured logs, persisted decisions, and evidence for each outcome.
- Offline operation with deterministic parsing and mandatory escalation when confidence is insufficient.

### Deferred Until Authoritative Data Exists

- Production bank connectivity and real money movement.
- Full three-way matching among invoice, purchase order, and goods receipt.
- Automated vendor onboarding or bank-account changes.
- Live foreign-exchange conversion.
- Learned fraud classification represented as a production-grade fraud model.
- Autonomous approval of novel vendors, changed payment instructions, or unsupported currencies.

## Stakeholders and Operating Model

| Stakeholder | Need | Proposed role |
|---|---|---|
| Accounts payable | Less re-keying and clearer exceptions | Own exception resolution and corrected data |
| VP approver | Concise evidence and policy-consistent decisions | Approve high-value or policy-routed invoices |
| Procurement/inventory | Accurate item and receipt context | Resolve stock, PO, and catalog mismatches |
| Treasury | Controlled, non-duplicative payments | Own payment policy, limits, and reconciliation |
| Internal audit/compliance | Reproducible decisions and retention | Review logs, policy versions, and access controls |
| IT/data owners | Reliable integrations and reference data | Own availability, schema contracts, and recovery |

Humans remain accountable for policy exceptions. The system recommends and executes only within explicitly delegated thresholds.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM fabricates or silently repairs data | Incorrect payment | Preserve source evidence, require structured output, validate deterministically, escalate low confidence |
| Prompt injection in invoice text | Policy bypass or data exposure | Treat document text as untrusted data; isolate tools and enforce graph routing in code |
| Legacy inventory is stale | Incorrect mismatch decisions | Record snapshot/version; distinguish source-system uncertainty from invoice error |
| Duplicate/revised invoice ambiguity | Double payment or wrong version | Vendor + invoice number identity, document hash, revision lineage, payment idempotency key |
| Model or network unavailable | Processing interruption | Deterministic parsers and rules; queue ambiguous cases for review/retry |
| Approval automation exceeds delegated authority | Governance failure | Policy-as-code, amount tiers, separation of duties, immutable decision record |
| Sensitive financial data leaks | Legal and reputational exposure | Least privilege, encryption, redacted telemetry, retention controls, approved model-data terms |
| Test set overfitting | Misleading prototype results | Holdout variants, mutation tests, human-labeled gold data, shadow-mode pilot |

## Assumptions Requiring Customer Decisions

1. Is inventory availability a valid reason to reject an invoice, or only a signal to reconcile receipt/PO records?
2. What are approval tiers beyond the stated $10,000 threshold, and who may approve each tier?
3. Which source is authoritative for vendor identity, purchase orders, goods receipt, pricing, tax, and currency?
4. How are revised invoices identified, and does a revision supersede or supplement the original?
5. What quantity, price, tax, and total tolerances are acceptable?
6. Which currencies and FX source are permitted?
7. What constitutes a duplicate across vendors, invoice numbers, dates, and amounts?
8. Which fraud indicators cause rejection versus a temporary hold?
9. What audit-retention, privacy, and data-residency requirements apply?
10. What service levels apply to routine, high-value, and payment-due exceptions?

## Delivery Recommendation

### Phase 1: Controlled Prototype

Run all supplied invoices through the complete graph, use only mock payment, label expected outcomes, and make failures reproducible. Demonstrate offline behavior and prove that hard controls cannot be bypassed by model output.

### Phase 2: Shadow Pilot

Process a representative historical sample alongside the existing workflow. Do not initiate real payments. Measure field accuracy, reviewer agreement, exception causes, cycle time, and potential savings by vendor and format.

### Phase 3: Limited Production

Enable straight-through handling only for known vendors, supported currencies, exact PO/receipt matches, low-value invoices, and high extraction confidence. Require human approval for all other cases and reconcile every payment.

### Phase 4: Controlled Expansion

Expand limits and formats based on measured performance. Add PO, receipt, vendor-master, contract, tax, and FX integrations before increasing autonomous authority.

## Decision

Proceed with a prototype and shadow pilot, subject to two conditions: first, define authoritative business rules and labeled expected outcomes; second, keep actual payment outside autonomous scope until accuracy, idempotency, audit, and segregation-of-duties controls have passed acceptance tests. This approach addresses the immediate cost and delay while keeping financial risk proportionate to evidence.