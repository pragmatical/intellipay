from enum import StrEnum
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReasoningMode(StrEnum):
    LOCAL = "local"
    LIVE = "live"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="INTELLIPAY_",
        extra="ignore",
    )

    reasoning_mode: ReasoningMode = ReasoningMode.LOCAL
    database_path: Path = Path(".intellipay/intellipay.db")
    xai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("XAI_API_KEY", "INTELLIPAY_XAI_API_KEY"),
    )
    xai_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-4.6"
    xai_timeout_seconds: float = 30.0
    max_extraction_repair_attempts: int = Field(default=1, ge=0, le=3)

    @field_validator("xai_api_key", mode="before")
    @classmethod
    def blank_api_key_is_missing(cls, value: object) -> object:
        return None if value == "" else value
