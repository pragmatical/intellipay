# IntelliPay

IntelliPay is a controlled, agent-assisted invoice-processing system for accounts payable. It turns heterogeneous invoice documents into evidence-backed decisions, routes uncertainty to people, and permits payment only after deterministic financial and policy gates pass.

The solution is being built for Acme Corp, where manual invoice handling currently contributes to a 30% error rate, a five-day processing cycle, and an estimated $2 million in annual avoidable cost. IntelliPay targets routine automation without giving an LLM authority over financial controls or cash movement.

> **Current status:** Stages 1 through 4 are implemented and engineering-verified. The complete supplied corpus is controlled deterministically, ambiguous extraction is bounded and safely traced, and escalations now pause for authenticated, policy-constrained human review before the same checkpoint resumes. Finance/domain label approval and observed reviewer timing and confidence baselines remain external follow-up work.

## Run the Reasoning Slice

Install the locked environment and run the default offline simulation:

```bash
uv sync --all-groups
uv run intellipay data/invoices/invoice_1001.txt
```

The result records `mode: local`, uses no network access, and conforms to the same validated invoice schema as live Grok.

To exercise real Grok behavior, provide the credential directly in your shell or through an uncommitted `.env`, then opt into live mode:

```bash
cp .env.example .env
# Set XAI_API_KEY in .env, then run:
uv run intellipay --reasoning-mode live data/invoices/invoice_1001.txt
```

Live mode calls the configurable xAI endpoint, currently `https://api.x.ai/v1`, using structured output from the configured model. It fails before making a request when `XAI_API_KEY` is absent. Run the offline provider contracts and the credentialed smoke test separately:

```bash
uv run pytest tests/reasoning/test_providers.py
XAI_API_KEY=... uv run pytest tests/reasoning/test_grok_live.py -m live
```

## Run the Review Interface

Process an invoice that requires review, configure a local reviewer identity, and start the server:

```bash
uv run intellipay data/invoices/invoice_1002.txt
export INTELLIPAY_REVIEWER_USERNAME=reviewer
export INTELLIPAY_REVIEWER_PASSWORD='replace-with-a-local-password'
uv run intellipay-review --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/reviews` and authenticate with those credentials. The interface shows the durable queue, original source, normalized payment facts, findings, rules, event timeline, constrained actions, and completed decision history. HTTP Basic authentication is a prototype boundary; production identity and delegated authority integration remain deferred.

## Solution Overview

IntelliPay combines three kinds of reasoning:

1. **Deterministic processing** parses known formats and enforces schema, arithmetic, inventory, duplicate, revision, and approval rules.
2. **Bounded xAI Grok reasoning** handles ambiguous extraction and critiques higher-risk recommendations through structured outputs and limited retries.
3. **Human judgment** resolves low-confidence, high-value, unsupported, or policy-sensitive cases through an explicit review route.

LangGraph coordinates these responsibilities as a typed, durable state machine. Each node receives limited tools, produces structured state, and follows explicit transition rules. The result is agentic where interpretation is useful and deterministic where financial safety requires predictability.

## End-to-End Workflow

The workflow moves through intake, extraction, deterministic validation, approval policy, human review when needed, idempotent payment, and reconciliation. Ambiguous extraction can enter a bounded Grok-assisted correction loop; hard failures and unresolved uncertainty cannot reach payment.

See the [detailed LangGraph workflow and routing logic](docs/analysis/proposed-solution.md#langgraph-workflow) in the proposed solution.

Every run preserves the source identity, canonical invoice, extraction evidence, validation findings, rules fired, route, model metadata, and payment result needed to explain and replay the decision.

## Processing Responsibilities

| Component | Responsibility | Allowed capabilities |
|---|---|---|
| Intake | Validate, hash, classify, and store the source | File store and document classifier |
| Extraction | Parse known formats and resolve ambiguous fields | Format parsers and structured reasoning provider |
| Extraction critic | Check schema, evidence, dates, item counts, and totals | Schema and arithmetic tools |
| Validation | Apply integrity, inventory, duplicate, revision, and policy checks | Read-only repositories and deterministic rules |
| Approval | Recommend approve, reject, or escalate | Risk calculator, approval policy, and bounded critique |
| Human review | Resolve cases outside delegated automation | Evidence view and review action store |
| Payment | Execute one authorized command | Idempotent mock payment adapter only |
| Reconciliation | Confirm the result and safely resolve unknown outcomes | Payment ledger and event history |

The model cannot query arbitrary databases, change policy, override hard findings, select unrestricted tools, authorize payment, or call the payment adapter.

## Decision Outcomes

| Outcome | Meaning | Typical reasons |
|---|---|---|
| `APPROVE` | Valid, sufficiently confident, and within delegated policy | Complete evidence, consistent totals, known inventory, permitted amount |
| `REJECT` | A deterministic failure makes the invoice invalid or unsafe | Negative quantity, invalid total, unavailable item, confirmed duplicate |
| `ESCALATE` | A person or unavailable business policy must resolve uncertainty | Low confidence, high value, revision ambiguity, unsupported currency |

Approval is not itself payment authorization. An approved invoice must still pass the payment command, authority, and idempotency gates.

## Intended User Experience

The primary application entry point accepts a local invoice and returns a structured result while persisting a complete trace:

```bash
python main.py --invoice_path=data/invoices/invoice_1001.txt
```

```json
{
	"run_id": "...",
	"invoice_number": "INV-1001",
	"status": "APPROVED",
	"risk": "LOW",
	"payment_status": "SUCCESS",
	"reasons": ["required fields present", "inventory checks passed"],
	"review_required": false
}
```

The review experience shows the source document, normalized fields and evidence, validation findings, policy rules, event history, and the actions currently permitted. Reviewers do not need application logs to understand why a case was routed to them.

## Core Design Principles

- **Rules decide hard constraints.** Financial integrity and authorization are code and versioned policy, not model opinion.
- **Grok resolves ambiguity.** Model use is narrow, structured, replaceable, and optional for offline operation.
- **Uncertainty becomes a route.** Low confidence triggers bounded repair or review rather than silent guessing.
- **Evidence remains attributable.** Accepted values retain their source and producer version.
- **Payment is least-privileged.** Only an authorized, idempotent command can reach the payment adapter.
- **Failures are explicit.** Retries are bounded, unavailable dependencies have defined routes, and interrupted runs resume from checkpoints.
- **Evaluation is versioned.** Results identify the data, parser, schema, policy, prompt, model, and inventory snapshot used.

## Technology Direction

| Concern | Prototype choice | Why |
|---|---|---|
| Runtime | Python | Matches the case requirements and document-processing ecosystem |
| Orchestration | LangGraph | Explicit routes, checkpoints, retries, and human interrupts |
| Model reasoning | xAI Grok behind `ReasoningProvider` | Structured ambiguity resolution without provider coupling |
| Persistence | SQLite | Local, transactional, inspectable, and sufficient for prototype scale |
| Document handling | Deterministic JSON, XML, CSV, TXT, and PDF adapters | Predictable offline processing for known formats |
| Policy | Versioned deterministic configuration | Reproducible decisions and reviewable authority limits |
| Payment | Idempotent mock adapter | End-to-end safety testing without real money movement |
| Evaluation | Offline fake provider plus opt-in live-model suite | Reproducible development with separate model-variance measurement |

## Safety and Control Model

IntelliPay treats documents, model outputs, reference data, human decisions, and payment as separate trust boundaries.

- Invoice text is untrusted and may contain prompt-injection instructions.
- Model responses must validate against the canonical schema before entering accepted graph state.
- Hard failures cannot transition to payment.
- Low-confidence required fields must retry or escalate.
- Secrets and live connections are injected into nodes and never serialized in graph state.
- Every payment command has a unique idempotency key.
- Unknown payment outcomes enter reconciliation and are never blindly resubmitted.
- Replay uses historical evidence but disables payment side effects.

## Evaluation Strategy

The solution is evaluated at unit, adapter-contract, persistence, graph-route, end-to-end, mutation, adversarial, failure-injection, performance, usability, and shadow-pilot layers.

The supplied invoice corpus provides the first functional acceptance set. Gold canonical invoices, findings, routes, and expected side effects will be versioned separately from test logic. Required quality gates include full payment-invariant compliance, full recall on labeled hard-control cases, no successful prompt injection that changes tools or routes, defined behavior for injected outages, and at least 95% required-field extraction accuracy overall.

See the [solution evaluation approach](docs/analysis/evaluation-approach.md) for datasets, metrics, model evaluation, quality gates, ownership, and reporting requirements.

## Prototype Scope

### Included

- Local ingestion for the supplied PDF, TXT, JSON, CSV, and XML invoices
- Canonical field and line-item extraction with source evidence
- SQLite inventory validation using the required seed data
- Integrity, arithmetic, inventory, duplicate, revision, and amount controls
- Bounded Grok extraction and decision critique with deterministic fallback
- Approve, reject, and escalate routes with human interrupt and resume
- Structured events, evaluation reports, and replay-safe traces
- Idempotent mock payment and reconciliation behavior
- A lightweight evidence-first review experience

### Deferred

- Real banking connectivity or autonomous real-money movement
- Enterprise identity, delegated authority integration, and production role management
- Purchase order, goods receipt, vendor master, contract, tax, and live FX integrations
- Managed queues, distributed workers, object storage, and production database infrastructure
- Automatic model training from reviewer corrections
- Production retention, residency, availability, and recovery controls pending owner decisions

## Repository Guide

| Path | Contents |
|---|---|
| [`context/`](context/) | Supplied case background, requirements, and reference snippets |
| [`data/invoices/`](data/invoices/) | Heterogeneous invoice fixtures and edge cases |
| [`docs/analysis/`](docs/analysis/) | Business case, proposed solution, architecture, and evaluation approach |
| [`docs/adr/`](docs/adr/) | Architecture decision records and trade-offs |
| [`docs/planning/`](docs/planning/) | Phased implementation plan and functional MVP exit gates |
| [`src/intellipay/`](src/intellipay/) | Runnable application package and reasoning adapters |
| [`tests/`](tests/) | Offline contracts and opt-in live Grok smoke coverage |
| [`.github/skills/`](.github/skills/) | Repository-specific Copilot workflows |
| [`.devcontainer/`](.devcontainer/) | Reproducible local development environment |

Workflow modules, migrations, evaluation assets, and the review interface will be added as implementation progresses.

## Implementation Sequence

The [functional MVP implementation plan](docs/planning/implementation-plan.md) defines detailed deliverables, measures, verification procedures, dependencies, risks, and exit gates for each phase. Stage 1 commands and evidence are recorded in the [Stage 1 verification record](docs/planning/stage-1-verification.md).

1. Build canonical models, format adapters, inventory persistence, deterministic validation, and mock payment.
2. Connect the vertical slice with LangGraph and prove approve, reject, escalate, and replay-safe payment routes.
3. Add the reasoning-provider boundary, structured Grok extraction, critic defects, bounded repair, and offline fallback.
4. Add human interrupt and resume, evidence-first review, structured telemetry, and evaluation reports.
5. Run the full supplied corpus, adversarial cases, failure injection, and a no-payment shadow pilot.

## Solution Documentation

- [Business case analysis](docs/analysis/business-case-analysis.md)
- [Proposed solution](docs/analysis/proposed-solution.md)
- [Architecture](docs/analysis/architecture.md)
- [Evaluation approach and needs](docs/analysis/evaluation-approach.md)
- [Functional MVP implementation plan](docs/planning/implementation-plan.md)
- [Architecture decision records](docs/adr/0001-use-langgraph-state-machine.md)
- [Original case context](context/README.md)