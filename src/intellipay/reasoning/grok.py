from typing import Any

from openai import OpenAI

from intellipay.config import ReasoningMode, Settings
from intellipay.reasoning.models import (
    DecisionCritique,
    DecisionCritiqueRequest,
    DecisionCritiqueResult,
    ExtractionCritique,
    ExtractionCritiqueRequest,
    ExtractionCritiqueResult,
    ExtractionRepairRequest,
    ExtractionRequest,
    ExtractionResult,
    InvoiceCandidate,
    TokenUsage,
)
from intellipay.reasoning.prompts import (
    CRITIQUE_SYSTEM_PROMPT,
    EXTRACTION_CRITIQUE_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    REPAIR_SYSTEM_PROMPT,
)


class GrokReasoningProvider:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        if settings.xai_api_key is None:
            raise ValueError("XAI_API_KEY is required when reasoning mode is live")
        self._settings = settings
        self._client = client or OpenAI(
            api_key=settings.xai_api_key.get_secret_value(),
            base_url=settings.xai_base_url,
            timeout=settings.xai_timeout_seconds,
        )

    def extract_invoice(self, request: ExtractionRequest) -> ExtractionResult:
        document = f"<invoice document_id={request.document_id!r}>\n{request.content}\n</invoice>"
        completion = self._client.beta.chat.completions.parse(
            model=self._settings.xai_model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": document,
                },
            ],
            response_format=InvoiceCandidate,
        )
        candidate = completion.choices[0].message.parsed
        if candidate is None:
            raise ValueError("Grok returned no structured invoice candidate")
        return ExtractionResult(
            mode=ReasoningMode.LIVE,
            provider="xai",
            model=completion.model,
            candidate=candidate,
            usage=self._token_usage(completion),
        )

    def critique_decision(self, request: DecisionCritiqueRequest) -> DecisionCritiqueResult:
        completion = self._client.beta.chat.completions.parse(
            model=self._settings.xai_model,
            messages=[
                {"role": "system", "content": CRITIQUE_SYSTEM_PROMPT},
                {"role": "user", "content": request.model_dump_json()},
            ],
            response_format=DecisionCritique,
        )
        critique = completion.choices[0].message.parsed
        if critique is None:
            raise ValueError("Grok returned no structured decision critique")
        return DecisionCritiqueResult(
            mode=ReasoningMode.LIVE,
            provider="xai",
            model=completion.model,
            critique=critique,
            usage=self._token_usage(completion),
        )

    def critique_extraction(self, request: ExtractionCritiqueRequest) -> ExtractionCritiqueResult:
        completion = self._client.beta.chat.completions.parse(
            model=self._settings.xai_model,
            messages=[
                {"role": "system", "content": EXTRACTION_CRITIQUE_PROMPT},
                {"role": "user", "content": request.model_dump_json()},
            ],
            response_format=ExtractionCritique,
        )
        critique = completion.choices[0].message.parsed
        if critique is None:
            raise ValueError("Grok returned no structured extraction critique")
        return ExtractionCritiqueResult(
            mode=ReasoningMode.LIVE,
            provider="xai",
            model=completion.model,
            critique=critique,
            usage=self._token_usage(completion),
        )

    def repair_invoice(self, request: ExtractionRepairRequest) -> ExtractionResult:
        completion = self._client.beta.chat.completions.parse(
            model=self._settings.xai_model,
            messages=[
                {"role": "system", "content": REPAIR_SYSTEM_PROMPT},
                {"role": "user", "content": request.model_dump_json()},
            ],
            response_format=InvoiceCandidate,
        )
        candidate = completion.choices[0].message.parsed
        if candidate is None:
            raise ValueError("Grok returned no repaired invoice candidate")
        return ExtractionResult(
            mode=ReasoningMode.LIVE,
            provider="xai",
            model=completion.model,
            candidate=candidate,
            usage=self._token_usage(completion),
        )

    @staticmethod
    def _token_usage(completion: Any) -> TokenUsage | None:
        usage = getattr(completion, "usage", None)
        if usage is None:
            return None
        prompt_details = getattr(usage, "prompt_tokens_details", None)
        return TokenUsage(
            input_tokens=usage.prompt_tokens,
            cached_input_tokens=getattr(prompt_details, "cached_tokens", 0) or 0,
            output_tokens=usage.completion_tokens,
        )
