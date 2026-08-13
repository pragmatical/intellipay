from decimal import Decimal

from intellipay.model_pricing import estimate_cost_usd, load_pricing_catalog
from intellipay.reasoning.models import TokenUsage


def test_checked_in_grok_pricing_handles_standard_cached_and_long_context_usage() -> None:
    catalog = load_pricing_catalog()

    assert catalog.effective_date == "2026-08-13"
    assert estimate_cost_usd(
        "grok-4.6",
        TokenUsage(input_tokens=100_000, cached_input_tokens=25_000, output_tokens=10_000),
        catalog,
    ) == Decimal("0.222500000000")
    assert estimate_cost_usd(
        "grok-4.6",
        TokenUsage(input_tokens=200_000, output_tokens=100_000),
        catalog,
    ) == Decimal("2.000000000000")


def test_unknown_model_usage_remains_unpriced() -> None:
    assert estimate_cost_usd("unknown-model", TokenUsage(input_tokens=10, output_tokens=10)) is None
