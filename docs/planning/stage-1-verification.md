# Stage 1 Verification

## Measured Outcome

Stage 1 produces one safe, replay-protected mock payment for INV-1001. A hard-control failure cannot pay, one controlled extraction ambiguity completes exactly one typed repair cycle, and a reconstructed workflow resumes its durable checkpoint without repeating payment.

## Clean Setup

```bash
cp .env.example .env
uv sync --all-groups
```

Keep `INTELLIPAY_REASONING_MODE=local` for deterministic offline verification. Add `XAI_API_KEY` only for an intentional live Grok run. Runtime state is created under `.intellipay/` and is ignored by Git.

## Automated Gate

```bash
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
```

The Stage 1 tests verify:

- INV-1001 reaches `APPROVE` and one successful mock payment.
- A duplicate submission returns the original payment identity and leaves one ledger row.
- A negative quantity reaches `REJECT` and leaves zero payment rows.
- An OCR-like subtotal ambiguity emits a typed defect, repairs once, and is deterministically revalidated.
- Versioned SQLite migration 1 can be applied repeatedly without changing seed inventory.
- Validation, decision, explicit payment authorization, and payment events occur in that order.
- A new workflow instance resumes a completed checkpoint without adding events or payment rows.
- Local and live reasoning adapters satisfy the same structured extraction contract.

## Inspectable Run

Start from an empty runtime database:

```bash
rm -f .intellipay/stage-1.db
uv run intellipay data/invoices/invoice_1001.txt \
  --reasoning-mode local \
  --database-path .intellipay/stage-1.db
```

Run the same command again. The second JSON result must retain the payment identity and set `payment_replayed` to `true`. The result also contains the inventory snapshot, policy rules fired, ordered event types, extraction defects, repair-attempt count, and payment-authorization status.

## Live Grok Check

The live check is opt-in and calls the paid xAI API:

```bash
set -a
source .env
set +a
uv run pytest -m live tests/reasoning/test_grok_live.py -v
```

The test must report `PASSED` for `test_real_grok_extracts_inv_1001_to_shared_contract`. Normal development and the Stage 1 safety gate remain deterministic and offline.

## Troubleshooting

- `XAI_API_KEY is required`: use local mode or add the key to the ignored `.env` file.
- Structured live-output failure: verify the configured model supports xAI structured outputs and rerun the focused live test.
- Unexpected replay result: remove only the chosen test database and rerun from clean state; do not remove repository fixtures.
- Schema failure: run the migration repeatability test before changing runtime data.