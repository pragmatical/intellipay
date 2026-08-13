# ADR-0004: Use SQLite for the Local Prototype

- **Status:** accepted
- **Date:** 2026-08-12
- **Decision owners:** To be assigned

## Context and Problem Statement

The prototype is a local Python service that needs durable workflow checkpoints, review tasks, invoice versions, findings, decisions, payment commands, audit events, and controlled reference data. It must be easy to run and inspect without production infrastructure while preserving relational constraints and a migration path to a managed transactional database.

## Decision Drivers

- Local, reproducible operation with minimal setup
- Durable checkpoints and review state across process restarts
- Transactions, foreign keys, uniqueness, and queryable audit data
- Sufficient capacity for the prototype corpus and evaluation harness
- Clear production migration boundary

## Considered Options

1. **SQLite:** One local relational database using WAL mode, constraints, migrations, and backups
2. **Managed PostgreSQL from the outset:** Use a production-oriented database for prototype and deployment
3. **Files and in-memory state:** Persist JSON artifacts and keep operational workflow state in process memory

## Decision Outcome

Chosen option: **SQLite**

Use SQLite for prototype operational data, LangGraph checkpoints, review state, payment ledger, audit events, and seeded reference data. Enable WAL mode and foreign keys, manage schema migrations, use transactions and unique indexes, and keep repository interfaces narrow enough to move production workloads to a managed relational database.

### Consequences

- **Positive:** The complete prototype remains local, inspectable, inexpensive, and simple to reproduce.
- **Positive:** Relational constraints can enforce duplicate, lineage, and payment invariants.
- **Negative:** Write concurrency, horizontal scaling, and some operational capabilities are limited.
- **Negative:** Production deployment requires database migration and operational redesign.
- **Follow-up:** Define migrations, backup and restore checks, repository contracts, and production migration criteria.

## Pros and Cons of the Options

### SQLite

- **Good:** Provides transactions and relational constraints without a separate service.
- **Bad:** Has limited concurrent-write throughput and production high-availability options.

### Managed PostgreSQL from the Outset

- **Good:** Better matches the expected production concurrency and operational model.
- **Bad:** Adds infrastructure, credentials, network dependency, and setup cost before prototype needs justify them.

### Files and In-Memory State

- **Good:** Has minimal database setup and produces directly inspectable artifacts.
- **Bad:** Makes transactional updates, uniqueness, resume behavior, and relational queries fragile.

## Confirmation

Restart tests must prove that checkpointed runs and review tasks resume correctly. Database tests must verify foreign keys, unique payment idempotency keys, transactional state and audit writes, migration repeatability, WAL configuration, and backup restoration.

## More Information

- [Architecture: data and persistence](../architecture/architecture.md#data-and-persistence)
- [Architecture: deployment shape](../architecture/architecture.md#deployment-shape)
- Production storage and availability objectives remain open decisions.
