from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SMART_REPLY_", env_file=".env", extra="ignore")

    environment: Literal["local", "dev", "prod"] = "local"
    api_key: str | None = None
    rate_limit_per_minute: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

