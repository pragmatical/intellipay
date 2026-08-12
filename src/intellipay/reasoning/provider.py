from typing import Protocol

from intellipay.reasoning.models import (
    DecisionCritiqueRequest,
    DecisionCritiqueResult,
    ExtractionCritique,
    ExtractionCritiqueRequest,
    ExtractionRepairRequest,
    ExtractionRequest,
    ExtractionResult,
)


class ReasoningProvider(Protocol):
    def extract_invoice(self, request: ExtractionRequest) -> ExtractionResult: ...

    def critique_extraction(self, request: ExtractionCritiqueRequest) -> ExtractionCritique: ...

    def repair_invoice(self, request: ExtractionRepairRequest) -> ExtractionResult: ...

    def critique_decision(self, request: DecisionCritiqueRequest) -> DecisionCritiqueResult: ...
