from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from pydantic import SecretStr

from intellipay.config import ReasoningMode, Settings
from intellipay.reasoning.grok import GrokReasoningProvider
from intellipay.reasoning.local import LocalReasoningProvider
from intellipay.reasoning.models import (
    ExtractionCritique,
    ExtractionDefect,
    ExtractionRepairRequest,
    ExtractionRequest,
)
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.models import Outcome


def test_mocked_live_adapter_completes_same_bounded_repair_graph(tmp_path: Path) -> None:
    source = Path("data/invoices/invoice_1001.txt").read_text()
    path = tmp_path / "ambiguous.txt"
    path.write_text(source.replace("$5,000.00", "$5,OOO.OO", 1))
    extraction_request = ExtractionRequest(document_id=path.name, content=path.read_text())
    local = LocalReasoningProvider()
    extraction = local.extract_invoice(extraction_request)
    defects = [
        ExtractionDefect(
            code="SUBTOTAL_INCONSISTENT_WITH_LINES",
            field="subtotal",
            message="Subtotal does not equal the sum of line items.",
        )
    ]
    repaired = local.repair_invoice(
        ExtractionRepairRequest(
            extraction=extraction_request,
            candidate=extraction.candidate,
            defects=defects,
            attempt=1,
        )
    )

    def parse_response(**kwargs):
        response_format = kwargs["response_format"]
        if response_format is ExtractionCritique:
            parsed = ExtractionCritique(defects=defects)
        elif parse.call_count == 3:
            parsed = repaired.candidate
        else:
            parsed = extraction.candidate
        return SimpleNamespace(
            model="grok-test",
            choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))],
        )

    parse = Mock(side_effect=parse_response)
    client = SimpleNamespace(
        beta=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)))
    )
    settings = Settings(
        database_path=tmp_path / "live.db",
        reasoning_mode=ReasoningMode.LIVE,
        xai_api_key=SecretStr("test-key"),
        xai_model="grok-test",
        _env_file=None,
    )

    result = InvoiceWorkflow(
        settings,
        provider=GrokReasoningProvider(settings, client=client),
    ).process(path)

    assert result.reasoning_mode is ReasoningMode.LIVE
    assert result.outcome is Outcome.APPROVE
    assert result.repair_attempts == 1
    assert result.invoice.subtotal == 5000
    assert parse.call_count == 3
