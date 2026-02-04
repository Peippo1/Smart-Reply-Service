from functools import lru_cache
from typing import Literal

try:  # Prefer real package but keep a fallback for offline test runs.
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover - fallback path
    from pydantic import BaseModel
    import os

    def SettingsConfigDict(**kwargs):  # type: ignore
        return kwargs

    class BaseSettings(BaseModel):  # type: ignore
        class Config:
            extra = "ignore"
            env_prefix = "SMART_REPLY_"

        def __init__(self, **data):  # type: ignore
            prefix = getattr(self.Config, "env_prefix", "")
            for field in self.__class__.model_fields:
                env_key = f"{prefix}{field}".upper()
                if env_key in os.environ and field not in data:
                    data[field] = os.environ[env_key]
            super().__init__(**data)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SMART_REPLY_", env_file=".env", extra="ignore")

    environment: Literal["local", "dev", "prod"] = "local"
    api_key: str | None = None
    rate_limit_per_minute: int = 60

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """
    Clear cached settings; useful in tests when env vars change.
    """
    get_settings.cache_clear()
