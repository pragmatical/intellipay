# Local Demo and Observability Guide

This guide runs the complete IntelliPay demonstration and inspects its durable observability data on one machine without Docker, cloud services, or network access during the presentation.

The default demo uses deterministic local reasoning and mock payment. It executes the real LangGraph workflow, persistence, review, policy, and payment-control paths without calling an external service.

## What Works Offline

| Capability | Available without Docker or network access |
|---|---|
| Eight-scenario executable demonstration | Yes |
| LangGraph workflow and SQLite checkpoints | Yes |
| Human-review web interface | Yes |
| Mock payment and replay controls | Yes |
| Per-invoice audit timeline | Yes |
| Redacted JSONL event export | Yes |
| Jaeger traces and Grafana metrics | No; these require an OTLP backend |
| Live xAI Grok reasoning | No; this requires network access and an API key |

> **Want LLM-based reasoning?** When network access is available, follow [Optionally Use the Real LLM](#optionally-use-the-real-llm) to configure `INTELLIPAY_REASONING_MODE` and `XAI_API_KEY` in the local `.env` file.

The SQLite event stream is the authoritative financial audit record. OpenTelemetry traces and metrics are optional operational evidence and do not affect workflow behavior.

## Prepare the Machine

IntelliPay requires:

- Git
- Python 3.12 or later
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)

Clone the repository and install its locked dependencies while package downloads are available:

```bash
git clone https://github.com/pragmatical/intellipay.git
cd intellipay
uv sync --locked --all-groups
```

After `uv sync` succeeds, the demo can run disconnected from the network. For a fully air-gapped machine, transfer the repository together with a populated `uv` cache or prebuilt environment; a fresh dependency installation cannot download packages without access to a package source.

## Run the Offline Demo

The built-in reasoning mode is `local`. If a `.env` file already exists from live-model testing, remove it or ensure it contains:

```dotenv
INTELLIPAY_REASONING_MODE=local
```

An exported shell value takes precedence over `.env`. Clear an old override when you want the file or built-in default to apply:

```bash
unset INTELLIPAY_REASONING_MODE
```

Start the presentation:

```bash
uv run intellipay-demo
```

Each run recreates only `.intellipay/demo.db`, executes eight narrated scenarios, and starts the review UI. Wait for:

```text
Uvicorn running on http://127.0.0.1:8001
```

Open [http://127.0.0.1:8001/reviews](http://127.0.0.1:8001/reviews) and sign in:

| Field | Value |
|---|---|
| Username | `reviewer` |
| Password | `intellipay-demo` |

Use another port if 8001 is occupied:

```bash
uv run intellipay-demo --port 8010
```

Run only the terminal scenarios when a browser is not needed:

```bash
uv run intellipay-demo --no-server
```

## Demonstrate the Controls

The terminal shows routine automation, replay protection, bounded reasoning, review routing, hard rejection, and invoice-revision safety. Use the review UI for these three cases:

1. Open **INV-9001** and compare the source evidence, normalized facts, `HIGH_VALUE` finding, policy route, and timeline.
2. Enter `Validated amount and inventory; approved for payment.` and select **APPROVE**. Confirm that the checkpoint resumes and one mock payment is recorded.
3. Open **INV-1002**. Show that insufficient stock disables **APPROVE** while reject and correction remain available.
4. Open **INV-1004**. Show that `INVOICE_VERSION_CONFLICT` prevents a second payment for the revised source.

Press `Ctrl+C` to stop the server. Run the command again to restore the same clean starting state.

## View Observability Without Docker

### Terminal Summary

The demo prints every scenario's outcome, payment status, replay status, findings, repair count, and reasoning-call count. Its final control summary lists payment totals and allowed review actions.

The final **Reasoning Cost Report** aggregates the same per-call usage stored in the reasoning traces. It reports input, cached-input, and output tokens; exact versus estimated calls; estimated API cost; and the pricing effective date and source. Local deterministic reasoning estimates token usage from the same prompts and structured request/response contracts as the live provider. Live xAI runs use token counts returned by the API.

Pricing is not stored in `.env`. The version-controlled [model pricing catalog](../src/intellipay/model_pricing.json) contains the currency, token unit, effective date, source URL, long-context threshold, and input/cached-input/output rates. Update and review that file when provider pricing changes. Cost is an estimate based on the catalog, not an xAI invoice; unknown models retain usage but are reported as unpriced.

Generate a machine-readable cost report across the complete supplied corpus:

```bash
uv run intellipay-evaluate --output .intellipay/evaluation-report.json
```

Open `.intellipay/evaluation-report.json` and inspect `reasoning_cost`. The section includes totals and a breakdown by reasoning operation.

### Review Timeline

The review UI is the easiest visual view. Each case shows original evidence, normalized payment facts, findings, policy routing, and the ordered run timeline. This view reads the same durable SQLite state used by the workflow.

Before starting the review UI, the demo writes `.intellipay/observability-report.md`. Open it in VS Code to see reasoning token usage, estimated API cost, per-operation cost breakdown, event counts, and the chronological redacted events captured during initial invoice processing. The report is a presentation snapshot; actions taken later in the review UI remain visible in the review timeline and can be captured with the event export command below.

### Redacted Event Stream

Export every durable demo event as newline-delimited JSON:

```bash
uv run intellipay-export-events \
  --database-path .intellipay/demo.db \
  --after-sequence 0 \
  --output .intellipay/events.jsonl
```

Pretty-print the export with Python already available in the project environment:

```bash
uv run python -m json.tool \
  --json-lines \
  .intellipay/events.jsonl
```

Search the file from VS Code or a terminal. For example:

```bash
rg 'payment|review|reasoning' .intellipay/events.jsonl
```

Each envelope includes a schema version, monotonic sequence, event ID, event type, occurrence time, trace and span correlation IDs when available, and redacted event data. Reviewer identities, rationales, and payment IDs are removed from this export.

When OpenTelemetry is enabled, the same workload emits `intellipay.reasoning.tokens` and `intellipay.reasoning.estimated_cost` metrics. The report remains available without an OTLP backend or Docker.

For incremental export, retain the last `sequence` value consumed and use it as the next cursor:

```bash
uv run intellipay-export-events \
  --database-path .intellipay/demo.db \
  --after-sequence LAST_SEQUENCE
```

This local workflow provides business and audit observability. Raw OpenTelemetry span waterfalls, latency histograms, and dashboards require an OTLP-compatible backend; the repository's Jaeger, Prometheus, and Grafana profile uses Docker and is not part of the disconnected path.

## Optionally Use the Real LLM

This mode is not offline. It calls a paid external xAI API and therefore requires network access and a valid key.

Copy the example configuration into the ignored local file:

```bash
cp .env.example .env
```

Set these values in `.env`:

```dotenv
INTELLIPAY_REASONING_MODE=live
XAI_API_KEY=your-xai-api-key
```

If the shell already exports `INTELLIPAY_REASONING_MODE`, clear it so `.env` can take effect:

```bash
unset INTELLIPAY_REASONING_MODE
uv run intellipay-demo
```

The demo has no reasoning-mode command-line option. Configuration precedence is an exported environment variable, `.env`, then the built-in `local` default.

Live model output must satisfy the same typed schemas and deterministic controls as local reasoning. The number of model and repair calls can vary: Grok may normalize the ambiguous amount during initial extraction and avoid the optional repair retry. The model cannot override inventory, duplicate, invoice-version, review, or payment-authorization controls.

Do not commit `.env` or print its API key. Return to disconnected execution by setting `INTELLIPAY_REASONING_MODE=local` or removing `.env`.

## Troubleshooting

- **`uv` is unavailable:** Install it before disconnecting, then reopen the terminal.
- **Dependency installation attempts network access:** Run `uv sync --locked --all-groups` while connected or supply a populated local package cache.
- **Port 8001 is occupied:** Stop the previous demo or use `--port 8010`.
- **The demo unexpectedly calls xAI:** Remove `.env`, set its reasoning mode to `local`, and clear any exported `INTELLIPAY_REASONING_MODE` value.
- **An old review link returns 404:** Open `/reviews` again. Every demo run recreates the database and review identifiers.
- **The JSONL export is empty:** Confirm that the demo ran and that `--database-path .intellipay/demo.db` was supplied.

For the presentation narrative and detailed approval walkthrough, see the [executable presentation guide](demo.md).
