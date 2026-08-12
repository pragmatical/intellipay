# Stage 3 Verification Record

**Verification date:** 2026-08-12  
**Scope:** Bounded ambiguity repair, reasoning failure handling, and protected decision boundaries

## Reproduce the Result

```bash
uv sync --all-groups
uv run pytest tests/workflow/test_stage_three.py tests/reasoning/test_grok_graph.py -q
uv run pytest -q
uv run ruff check .
uv run ruff format --check src tests
```

The default suite is offline. [The mocked-live graph test](../../tests/reasoning/test_grok_graph.py) exercises the xAI adapter through the same extraction, typed critique, repair, revalidation, decision, authorization, and payment graph without network access. The paid real-Grok smoke test remains separately opt-in.

## Measured Evidence

| Measure | Result |
|---|---:|
| Focused Stage 3 and provider-parity cases | 9 passed |
| Complete offline suite | 48 passed |
| Successful repair cases producing typed defects | 100% |
| Repair attempts above configured limit | 0 |
| Unresolved repairs reaching review | 100% |
| Injected extraction and critique outages reaching escalation | 100% |
| Malformed provider output entering accepted graph state | 0 |
| Prompt-injection boundary violations | 0 |
| Decision critique weakening deterministic escalation | 0 |
| Network calls required by default suite | 0 |

## Executable Paths

- A controlled OCR-like subtotal error creates `SUBTOTAL_INCONSISTENT_WITH_LINES`, repairs once, reruns deterministic validation, and approves only after findings clear.
- An unresolved repair reaches `REPAIR_EXHAUSTED` after the configured one-attempt limit and creates a durable review task without payment.
- Extraction timeout uses the deterministic known-format adapter, records `MODEL_UNAVAILABLE`, and escalates without payment.
- Invalid structured output is rejected by Pydantic at the graph boundary, records `MODEL_OUTPUT_INVALID`, and cannot enter accepted state.
- Critique or repair failure preserves the candidate and source, records a redacted failure trace, and escalates.
- Embedded instructions cannot change policy rules, graph edges, available tools, or payment authorization.
- Enhanced-review critique runs once for high-value cases. Successful, permissive, malformed, or unavailable critique cannot weaken the deterministic route.

## Trace Contract

Each reasoning operation records its operation, attempt, status, provider mode, model when available, prompt version, measured latency, SHA-256 request fingerprint, optional token usage, and error type. Raw invoice content and credentials are not copied into the trace. Provider events are persisted with the run and returned as typed `reasoning_trace` entries.

## Live Provider

Live mode remains opt-in through `INTELLIPAY_REASONING_MODE=live` and `XAI_API_KEY`. Missing credentials fail closed before a request. The existing paid smoke test can be run explicitly:

```bash
XAI_API_KEY=... uv run pytest tests/reasoning/test_grok_live.py -m live
```

That paid test was not rerun as part of this Stage 3 verification pass.