# Stage 4 Verification Record

**Verification date:** 2026-08-12  
**Scope:** Authenticated exception review, durable disposition, and checkpoint resume

## Reproduce the Result

```bash
uv sync --all-groups
uv run pytest tests/review/test_review_app.py tests/workflow/test_stage_four.py -q
LANGGRAPH_STRICT_MSGPACK=true uv run pytest tests/review/test_review_app.py tests/workflow/test_stage_four.py -q
uv run pytest -q
uv run ruff check .
uv run ruff format --check src tests
```

To exercise the interface, process an escalated fixture and start the server with `INTELLIPAY_REVIEWER_USERNAME` and `INTELLIPAY_REVIEWER_PASSWORD` configured:

```bash
uv run intellipay data/invoices/invoice_1002.txt
uv run intellipay-review --host 0.0.0.0 --port 8000
```

## Measured Evidence

| Measure | Result |
|---|---:|
| Focused review workflow and HTTP cases | 4 passed |
| Complete offline suite | 52 passed |
| Review actions with actor and rationale | 100% |
| Duplicate decisions under repeated submission | 0 |
| Duplicate payments under review replay | 0 |
| Disallowed approvals executable through HTTP | 0 |
| Editor diagnostics | 0 |
| Desktop and mobile horizontal overflow findings | 0 |

The complete suite remains offline and network-free. Ruff lint passed and all 37 Python files were formatted. FastAPI's compatibility `TestClient` emits one upstream Starlette deprecation warning about future `httpx2` migration; application behavior is unaffected.

## Executable Paths

- Escalated runs pause at a LangGraph `interrupt` and retain their typed checkpoint.
- The checkpoint serializer explicitly allows only IntelliPay's typed state modules; interrupt and resume pass with LangGraph strict MessagePack enforcement enabled.
- SQLite stores priority, status, allowed actions, actor, rationale, disposition, and timestamps.
- A permitted decision resumes the same run. Soft approval passes through the existing authorization and idempotent payment nodes; rejection and correction requests finish without payment.
- Review writes use compare-and-set semantics. Repeating the identical submission returns the persisted result and does not duplicate the audit event or payment.
- Hard findings, model uncertainty, unsupported currency, duplicate invoices, version conflicts, and insufficient stock cannot be human-approved.
- HTTP Basic identity, a task-bound CSRF token, server-side action validation, and POST/redirect/get protect the prototype review surface.

## Interface Verification

Browser automation inspected the queue and invoice detail at 1440 × 900 and 390 × 844. The detail exposes original source evidence, canonical payment facts, findings, policy rules, event history, rationale, action effects, and disabled-action explanations. Both viewports reported document `scrollWidth == clientWidth`, no overflowing elements, and the prohibited approval control disabled.

Queue empty, open, completed, and all filters are implemented. Unknown cases and invalid or stale actions return explicit HTTP errors rather than permissive fallbacks.

## Remaining Human Evidence

The engineering and automated usability gate is passed. Active handling time, reviewer confidence, requests for help, and comprehension accuracy require sessions with accounts-payable participants and are not claimed by this verification. Finance/domain approval of the 20 Stage 2 draft labels also remains pending.