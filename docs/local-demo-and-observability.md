# Local Demo and Observability Guide

This guide runs the complete IntelliPay demonstration and inspects its durable observability data on one machine without Docker, cloud services, or network access during the presentation.

The default demo uses deterministic local reasoning and mock payment. It executes the real LangGraph workflow, persistence, review, policy, and payment-control paths without calling an external service.

The interactive demo uses eight curated scenarios to show distinct outcomes and shared-state controls without repeating format variants. The corpus evaluation separately processes all 20 supplied files from clean state. Use both to demonstrate workflow depth and complete file coverage.

## What Works Offline

| Capability | Available without Docker or network access |
|---|---|
| Eight-scenario executable demonstration | Yes |
| Isolated evaluation of all 20 supplied files | Yes |
| LangGraph workflow and SQLite checkpoints | Yes |
| Human-review web interface | Yes |
| Mock payment and replay controls | Yes |
| Per-invoice audit timeline | Yes |
| Redacted JSONL event export | Yes |
| Mocked xAI Grok reasoning | Yes; deterministic local simulation |
| Live xAI Grok reasoning | No; this requires network access and an API key |
| Jaeger traces and Grafana metrics | No; these require an OTLP backend |

> **Configure LLM-based reasoning:** When network access is available, copy `.env.example` to `.env`, set `INTELLIPAY_REASONING_MODE=live` and `XAI_API_KEY`, clear any shell override with `unset INTELLIPAY_REASONING_MODE`, then run `uv run intellipay-demo`. See [Optionally Use the Real LLM](#optionally-use-the-real-llm) for the complete steps and safety boundaries.

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

## Evaluate All 20 Invoice Files

Run the complete supplied corpus before or after the interactive demo:

```bash
INTELLIPAY_REASONING_MODE=local uv run intellipay-evaluate \
  --output .intellipay/evaluation-report.json
```

Open [`.intellipay/evaluation-report.json`](../.intellipay/evaluation-report.json) and confirm:

- `total_cases` and `passed_cases` are both `20`.
- `failed_cases`, `prohibited_payment_count`, and `batch_error_count` are `0`.
- `route_agreement_rate`, `finding_agreement_rate`, and `hard_control_recall_rate` are `1.0`.
- `reasoning_cost` contains token totals, estimated cost, and the per-operation breakdown.

Each corpus case runs against a fresh temporary database. This isolates parser, validation, route, and payment expectations for every file, including equivalent PDF/TXT and PDF/JSON variants. Stateful duplicate, replay, and revision-conflict behavior is exercised by the eight-scenario demo and dedicated workflow tests.

## Run the Demonstration

Use this sequence during the presentation:

1. Run the processor and wait for all eight invoice scenarios to complete.
2. Validate the generated Markdown observability report.
3. Use the approval UI against the same persisted workflow state.

Keep the demo command running throughout all three steps. After processing, it becomes the web server for the approval UI.

### 1. Run the Processor

The built-in reasoning mode is `local`. If a `.env` file already exists from live-model testing, remove it or ensure it contains:

```dotenv
INTELLIPAY_REASONING_MODE=local
```

An exported shell value takes precedence over `.env`. Clear an old override when you want the file or built-in default to apply:

```bash
unset INTELLIPAY_REASONING_MODE
```

Start the deterministic local presentation. This command overrides any live reasoning mode in `.env` for this run:

```bash
INTELLIPAY_REASONING_MODE=local uv run intellipay-demo
```

> **Generated report:** After all eight scenarios finish, open [`.intellipay/observability-report.md`](../.intellipay/observability-report.md) from the repository root. The file is recreated on every demo run before the approval UI starts.

Each run recreates only `.intellipay/demo.db`, executes eight narrated scenarios, writes the observability report, and starts the review UI. Follow the `[1/8]` through `[8/8]` progress messages and confirm the terminal prints:

```text
OBSERVABILITY REPORT
  Captured events: ...
  Markdown: .intellipay/observability-report.md

Uvicorn running on http://127.0.0.1:8001
```

The command has not hung when Uvicorn starts. Leave it running while you inspect the report and use the UI. Open a second terminal only for optional event-export commands.

### 2. Validate the Observability Report

Open [`.intellipay/observability-report.md`](../.intellipay/observability-report.md) in VS Code. It is generated from the same SQLite database that the processor and approval UI use.

Confirm the report contains:

1. **Summary:** a nonzero total event count and a monotonic sequence range.
2. **Reasoning Usage and Estimated Cost:** usage basis, reasoning calls, input/cached-input/output tokens, total estimated API cost, pricing effective date and source, and per-operation costs.
3. **Event Types:** counts for the durable workflow events captured during the eight scenarios.
4. **Captured Events:** chronological event envelopes with sequence, occurrence time, event type, and redacted data.
5. **Redaction:** sensitive payment IDs, reviewer identities, and rationales appear as `[REDACTED]` when those fields are present.

Local-mode token usage is estimated from the production prompts and structured contracts. Live xAI runs use provider-reported token counts. Cost is a catalog-based estimate, not a provider invoice.

The Markdown file is a snapshot of initial processing. Approval actions performed next are visible immediately in each review's timeline; use the incremental export described under [Redacted Event Stream](#redacted-event-stream) when a post-approval file artifact is needed.

### 3. Use the Approval UI

Open [http://127.0.0.1:8001/reviews](http://127.0.0.1:8001/reviews) and sign in:

| Field | Value |
|---|---|
| Username | `reviewer` |
| Password | `intellipay-demo` |

Walk through these controls in order:

1. Open **INV-9001** and compare the source evidence, normalized facts, `HIGH_VALUE` finding, policy route, and timeline.
2. Enter `Validated amount and inventory; approved for payment.` and select **APPROVE**. Confirm that the checkpoint resumes and one mock payment is recorded.
3. Open **INV-1002**. Show that insufficient stock disables **APPROVE** while reject and correction remain available.
4. Open **INV-1004**. Show that `INVOICE_VERSION_CONFLICT` prevents a second payment for the revised source.

Press `Ctrl+C` in the original terminal when the presentation is complete. Run the command again to recreate a clean, predictable demo state.

### Alternate Runs

Use another port if 8001 is occupied:

```bash
uv run intellipay-demo --port 8010
```

Run only the terminal scenarios when a browser is not needed:

```bash
uv run intellipay-demo --no-server
```

## View Observability Without Docker

### Terminal Summary

The demo prints every scenario's outcome, payment status, replay status, findings, repair count, and reasoning-call count. Its final control summary lists payment totals and allowed review actions.

The final **Reasoning Cost Report** aggregates the same per-call usage stored in the reasoning traces. It reports input, cached-input, and output tokens; exact versus estimated calls; estimated API cost; and the pricing effective date and source. Local deterministic reasoning estimates token usage from the same prompts and structured request/response contracts as the live provider. Live xAI runs use token counts returned by the API.

Pricing is not stored in `.env`. The version-controlled [model pricing catalog](../src/intellipay/model_pricing.json) contains the currency, token unit, effective date, source URL, long-context threshold, and input/cached-input/output rates. Update and review that file when provider pricing changes. Cost is an estimate based on the catalog, not an xAI invoice; unknown models retain usage but are reported as unpriced.

The complete 20-file evaluation described under [Evaluate All 20 Invoice Files](#evaluate-all-20-invoice-files) writes a machine-readable report whose `reasoning_cost` section includes totals and a breakdown by reasoning operation.

### Review Timeline

Each approval case shows original evidence, normalized payment facts, findings, policy routing, and the ordered run timeline. This is the easiest visual view for events created after the initial Markdown report, and it reads the same durable SQLite state used by the workflow.

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
