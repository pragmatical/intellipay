from typing import Protocol

from intellipay.reasoning.models import (
    DecisionCritiqueRequest,
    DecisionCritiqueResult,
    ExtractionRequest,
    ExtractionResult,
)


class ReasoningProvider(Protocol):
    def extract_invoice(self, request: ExtractionRequest) -> ExtractionResult: ...

    def critique_decision(self, request: DecisionCritiqueRequest) -> DecisionCritiqueResult: ...
