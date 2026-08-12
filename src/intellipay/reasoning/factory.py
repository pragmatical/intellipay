from intellipay.config import ReasoningMode, Settings
from intellipay.reasoning.grok import GrokReasoningProvider
from intellipay.reasoning.local import LocalReasoningProvider
from intellipay.reasoning.provider import ReasoningProvider


def create_reasoning_provider(settings: Settings) -> ReasoningProvider:
    if settings.reasoning_mode is ReasoningMode.LOCAL:
        return LocalReasoningProvider()
    return GrokReasoningProvider(settings)
