from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import SecretStr

from intellipay.config import ReasoningMode, Settings
from intellipay.reasoning.factory import create_reasoning_provider
from intellipay.reasoning.grok import GrokReasoningProvider
from intellipay.reasoning.local import LocalReasoningProvider
from intellipay.reasoning.models import (
    Currency,
    ExtractionRequest,
    InvoiceCandidate,
    LineItem,
)

FIXTURE = Path("data/invoices/invoice_1001.txt")


def extraction_request() -> ExtractionRequest:
    return ExtractionRequest(document_id=FIXTURE.name, content=FIXTURE.read_text())


def invoice_candidate() -> InvoiceCandidate:
    return InvoiceCandidate(
        vendor_name="Widgets Inc.",
        invoice_number="INV-1001",
        invoice_date="2026-01-15",
        due_date="2026-02-01",
        currency=Currency.USD,
        subtotal="5000.00",
        tax="0.00",
        total_amount="5000.00",
        payment_terms="Net 15",
        line_items=[
            LineItem(item="WidgetA", quantity="10", unit_price="250.00"),
            LineItem(item="WidgetB", quantity="5", unit_price="500.00"),
        ],
    )


def test_local_mode_is_default_and_extracts_fixture_deterministically() -> None:
    settings = Settings(_env_file=None)

    provider = create_reasoning_provider(settings)
    result = provider.extract_invoice(extraction_request())

    assert isinstance(provider, LocalReasoningProvider)
    assert result.mode is ReasoningMode.LOCAL
    assert result.provider == "simulated"
    assert result.candidate == invoice_candidate()


def test_live_mode_fails_closed_without_xai_api_key() -> None:
    settings = Settings(reasoning_mode=ReasoningMode.LIVE, _env_file=None)

    with pytest.raises(ValueError, match="XAI_API_KEY is required"):
        create_reasoning_provider(settings)


def test_live_mode_uses_xai_structured_output_contract() -> None:
    candidate = invoice_candidate()
    parse = Mock(
        return_value=SimpleNamespace(
            model="grok-test",
            choices=[SimpleNamespace(message=SimpleNamespace(parsed=candidate))],
        )
    )
    client = SimpleNamespace(
        beta=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)))
    )
    settings = Settings(
        reasoning_mode=ReasoningMode.LIVE,
        xai_api_key=SecretStr("test-key"),
        xai_model="grok-test",
        _env_file=None,
    )

    result = GrokReasoningProvider(settings, client=client).extract_invoice(extraction_request())

    assert result.mode is ReasoningMode.LIVE
    assert result.provider == "xai"
    assert result.model == "grok-test"
    assert result.candidate == candidate
    parse.assert_called_once()
    call = parse.call_args.kwargs
    assert call["model"] == "grok-test"
    assert call["response_format"] is InvoiceCandidate
    assert "<invoice document_id='invoice_1001.txt'>" in call["messages"][1]["content"]
