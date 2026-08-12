# ADR-0009: Use OpenTelemetry with Optional Trace Backends

- **Status:** accepted
- **Date:** 2026-08-12
- **Decision owners:** To be assigned

## Context and Problem Statement

IntelliPay needs locally demonstrable traces and metrics for workflow latency, graph routing, bounded reasoning, review resume, and payment outcomes. The same instrumentation should support a hosted analysis service later without coupling financial controls to one vendor or making an exporter part of the payment path. Durable business events must remain queryable and replayable when telemetry is disabled or unavailable.

## Decision Drivers

- Run and inspect observability locally without an external account or internet access
- Preserve vendor choice for trace, metric, and analysis backends
- Keep telemetry exporter failures outside workflow routing and payment authority
- Correlate operational spans with versioned durable events without recording invoice or reviewer content
- Bound metric cardinality and redact financial, model, and identity data by default

## Considered Options

1. **OpenTelemetry SDK and Collector with optional backends:** Instrument the application once, export through OTLP, and fan out to local or hosted stores
2. **LangSmith-only tracing:** Use the LangChain ecosystem's hosted tracing path as the required observability runtime
3. **Durable events only:** Analyze SQLite business events without operational traces or metrics

## Decision Outcome

Chosen option: **OpenTelemetry SDK and Collector with optional backends**

Instrument workflow, graph-node, reasoning, review, storage, and payment boundaries with the OpenTelemetry API and SDK. Telemetry is disabled by default. When enabled, the application exports OTLP/HTTP to a Collector; the local profile sends traces to Jaeger and exposes metrics to Prometheus for Grafana. LangSmith may be added as an optional Collector destination or framework integration, but application correctness does not depend on it.

SQLite business events remain the authoritative financial audit record. Each new event has a stable event ID, schema version, monotonic sequence, and active trace/span correlation when available. A cursor-based JSONL export provides a structured analytics ingestion contract with reviewer identities, rationales, and payment IDs redacted by default.

### Consequences

- **Positive:** The same application instrumentation supports local inspection and future hosted backends.
- **Positive:** Traces can be correlated with durable events while audit history remains available independently.
- **Positive:** Tests can validate span topology, metrics, and redaction entirely in memory.
- **Negative:** The local profile adds four containers and operational configuration.
- **Negative:** Explicit graph instrumentation may overlap with future LangGraph-native spans and requires naming governance.
- **Follow-up:** Add FastAPI server spans, exporter-failure tests, dashboards, retention policy, and optional LangSmith fan-out only when there is a concrete hosted-analysis requirement.

## Pros and Cons of the Options

### OpenTelemetry SDK and Collector with Optional Backends

- **Good:** Vendor-neutral, locally inspectable, standard OTLP transport, and backend fan-out without application changes.
- **Bad:** Requires explicit instrumentation and Collector configuration.

### LangSmith-Only Tracing

- **Good:** Rich LangGraph-specific trace exploration and evaluation workflows.
- **Bad:** The standard hosted experience requires an external account and network access; self-hosting is not proportionate to this prototype.

### Durable Events Only

- **Good:** Simple, transactional, and already aligned with the financial audit boundary.
- **Bad:** Does not expose latency distributions, parent-child execution topology, or exporter-compatible operational metrics.

## Confirmation

In-memory contracts must prove a root workflow span, direct graph-node children, nested reasoning spans, shared run and trace correlation, bounded metrics, and absence of invoice content in span attributes. Persistence tests must prove event migration, stable IDs, schema versions, trace/span correlation, cursor ordering, and default export redaction. `docker compose config` and an end-to-end local smoke run must prove the Collector receives OTLP, Jaeger displays traces, and Prometheus exposes IntelliPay metrics. Workflow tests must continue to pass with telemetry disabled.

## More Information

- [Remaining implementation backlog](../planning/remaining-implementation-backlog.md)
- [Architecture](../analysis/architecture.md)
- [ADR-0001: Use a LangGraph state machine](0001-use-langgraph-state-machine.md)
- [ADR-0004: Use SQLite for local prototype](0004-use-sqlite-for-local-prototype.md)