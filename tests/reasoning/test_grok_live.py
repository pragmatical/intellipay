import os
from pathlib import Path

import pytest

from intellipay.config import ReasoningMode, Settings
from intellipay.model_pricing import estimate_cost_usd
from intellipay.reasoning import create_reasoning_provider
from intellipay.reasoning.models import ExtractionRequest

pytestmark = pytest.mark.live


@pytest.mark.skipif(not os.getenv("XAI_API_KEY"), reason="XAI_API_KEY is not configured")
def test_real_grok_extracts_inv_1001_to_shared_contract() -> None:
    path = Path("data/invoices/invoice_1001.txt")
    settings = Settings(reasoning_mode=ReasoningMode.LIVE, _env_file=None)

    result = create_reasoning_provider(settings).extract_invoice(
        ExtractionRequest(document_id=path.name, content=path.read_text())
    )

    assert result.mode is ReasoningMode.LIVE
    assert result.provider == "xai"
    assert result.usage is not None
    assert result.usage.estimated is False
    assert result.usage.input_tokens > 0
    assert result.usage.output_tokens > 0
    estimated_cost = estimate_cost_usd(settings.xai_model, result.usage)
    assert estimated_cost is not None
    assert estimated_cost > 0
    assert result.candidate.invoice_number == "INV-1001"
    assert result.candidate.total_amount == 5000
    assert {item.item for item in result.candidate.line_items} == {"WidgetA", "WidgetB"}
