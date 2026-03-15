from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ml_agent"
    alembic_database_url: str | None = None
    default_marketplace: str = "mercadolivre"
    mercadolivre_api_base: str = "https://api.mercadolibre.com"
    mercadolivre_auth_base: str = "https://auth.mercadolivre.com.br"
    mercadolivre_app_id: str | None = None
    mercadolivre_client_secret: str | None = None
    mercadolivre_redirect_uri: str | None = None
    mercadolivre_access_token: str | None = None
    mercadolivre_refresh_token: str | None = None
    shopee_api_base: str = "https://partner.shopeemobile.com"
    shopee_access_token: str | None = None
    pricing_worker_bin: str = "../workers/pricing_worker/target/debug/pricing_worker"
    request_timeout_seconds: float = 15.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
