from typing import Optional, List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    broker_url: str
    celery_broker_url: str
    celery_result_backend: str

    auth0_domain: str
    api_identifier: str
    algorithms: List[str] = ["RS256"]

    model_dir: str = "models"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("broker_url", "celery_broker_url", "celery_result_backend", "auth0_domain", "api_identifier", mode="before")
    @classmethod
    def must_be_provided(cls, v, info):
        if not v:
            raise ValueError(f"{info.field_alias} must be set via .env or env vars")
        return v

settings = Settings()
