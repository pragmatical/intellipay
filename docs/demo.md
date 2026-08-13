# IntelliPay Executable Presentation

The executable presentation runs the real invoice workflow in deterministic local mode, prints a business-focused narrative, prepares review cases, and starts the existing approval interface against the same isolated database.

## Start the Presentation

Install the locked environment, then run one command from the repository root:

```bash
uv sync --all-groups
uv run intellipay-demo
```

The runner resets only `.intellipay/demo.db`, creates derived demo inputs under `.intellipay/demo-inputs/`, executes the workflow, and starts the review UI at `http://127.0.0.1:8001/reviews`.

Use these local demonstration credentials:

- **Username:** `reviewer`
- **Password:** `intellipay-demo`

Press `Ctrl+C` when the presentation is complete. Run the same command again to recreate a clean, predictable demo state.

### Use the Actual xAI Model

Local deterministic reasoning is the default. To run the complete presentation through the live xAI adapter, create an ignored `.env` from `.env.example` and set:

```dotenv
INTELLIPAY_REASONING_MODE=live
XAI_API_KEY=your-xai-api-key
```

Run `uv run intellipay-demo` with the same options shown above. The runner has no reasoning-mode option: an exported environment variable takes precedence over `.env`, and `.env` takes precedence over the built-in `local` default. Run `unset INTELLIPAY_REASONING_MODE` first if the current shell already exports a value that should not override `.env`.

Live model output must satisfy the same typed schemas and deterministic controls, but the number of reasoning and repair calls may vary. A model that resolves INV-9002 during initial extraction will not consume the optional repair attempt. Live execution calls a paid external API.

## What the Runner Demonstrates

The terminal narrates each result and its business impact:

1. **Routine automation:** INV-1001 passes extraction, validation, policy, authorization, and mock payment.
2. **Replay protection:** Submitting INV-1001 again reuses the persisted payment rather than paying twice.
3. **Bounded agentic correction:** INV-9002 contains an ambiguous amount; the structured critic and one repair attempt resolve it.
4. **Approvable human review:** INV-9001 is valid but high value, so payment waits for delegated approval.
5. **Policy-blocked human review:** INV-1002 has insufficient inventory, so approval remains unavailable.
6. **Hard rejection:** INV-1009 contains invalid financial data and cannot reach payment.
7. **Original invoice payment:** The original INV-1004 version is accepted and paid once.
8. **Revision safety:** The conflicting INV-1004 revision escalates and cannot create another payment.

The final control summary reports persisted payment count, open review tasks, finding codes, and the actions allowed for each review.

## Approval UI Walkthrough

### 1. Approve a Valid High-Value Invoice

1. Open `http://127.0.0.1:8001/reviews` and authenticate with the demo credentials.
2. Select **INV-9001**.
3. Compare the original source with normalized payment facts.
4. Confirm that `HIGH_VALUE` is the only review reason and that **APPROVE** is available.
5. Enter a rationale of at least ten characters, such as `Validated amount and inventory; approved for payment.`
6. Select **APPROVE**.
7. Confirm the completed review state and timeline. The same checkpoint resumes through payment authorization and one mock payment.

### 2. Show a Non-Overridable Control

1. Return to the queue and select **INV-1002**.
2. Show the insufficient-stock evidence and policy findings.
3. Confirm that **APPROVE** is disabled and the interface explains why.
4. Point out that the model critique and reviewer cannot weaken the inventory control.

### 3. Show Revision Safety

1. Return to the queue and select **INV-1004** with `INVOICE_VERSION_CONFLICT`.
2. Confirm that payment was not attempted for the revision.
3. Use the timeline to explain that business identity and persisted payment history prevent duplicate cash movement.

## Useful Options

Run the narrated workflow without starting a server:

```bash
uv run intellipay-demo --no-server
```

Use another local port:

```bash
uv run intellipay-demo --port 8010
```

The runner always resets the fixed `.intellipay/demo.db` before processing. Stop an existing demo server before starting another presentation session.

## Optional Local Observability

Start the local observability profile before the demo to send workflow, node, and reasoning telemetry through the Collector:

```bash
docker compose -f compose.observability.yaml up -d
export INTELLIPAY_TELEMETRY_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
uv run intellipay-demo
```

Use Jaeger at `http://localhost:16686` for traces and Grafana at `http://localhost:3000` for metrics. Observability is optional and cannot change workflow routing or payment behavior.