# Stage 2 Verification Record

**Verification date:** 2026-08-12  
**Scope:** Deterministic control of the complete supplied invoice corpus

## Reproduce the Result

Install the locked environment, run the complete offline suite, and regenerate the corpus report:

```bash
uv sync --all-groups
uv run pytest -q
uv run ruff check .
uv run ruff format --check src tests
uv run intellipay-evaluate --output evaluation/stage2-report.json
```

The evaluator validates [the versioned manifest](../../evaluation/stage2-manifest.json), processes each case against an isolated database, continues after per-case exceptions, and writes [the machine-readable report](../../evaluation/stage2-report.json).

## Measured Evidence

| Measure | Result |
|---|---:|
| Supplied files evaluated | 20 of 20 |
| Terminal outcomes | 20 of 20 |
| Route agreement | 100% |
| Finding agreement | 100% |
| Hard-control recall | 100% (4 of 4 isolated rejection cases) |
| Prohibited payments | 0 |
| Batch errors | 0 |
| Route distribution | 10 approve, 6 escalate, 4 reject |
| Offline automated tests | 39 passed |

JSON, CSV, XML, TXT, and image-only PDF files use deterministic adapters. PDF processing uses repository-declared PDFium rendering and headless ONNX OCR dependencies; it does not depend on undeclared host OCR binaries.

## Operational Sequences

- INV-1004 original followed by R1 records `INVOICE_VERSION_CONFLICT`; only the original can pay.
- INV-1011 and INV-1012 TXT followed by PDF record `DUPLICATE_INVOICE`; each sequence creates at most one payment.
- Exact-source replay remains idempotent and returns the existing payment without another side effect.
- INV-1013 JSON and PDF normalize to equivalent payment facts. Decimal formatting differences do not create a false version conflict, and both isolated cases reject before payment for their existing hard findings.
- Every escalation creates one durable open review task.

## Label Status

All 20 seed labels remain `draft` pending finance/domain approval. The implementation gate is satisfied against those versioned draft labels, but label approval is an external sign-off item rather than an engineering claim.

The supplied INV-1013 JSON and PDF files were previously described as conflicting. Deterministic extraction shows equivalent invoice identity, line items, amounts, dates, currency, and terms; only decimal presentation differs. The manifest therefore classifies them as equivalent variants. A separate genuinely conflicting fixture is still needed to measure same-identity conflict detection beyond the INV-1004 revision case.