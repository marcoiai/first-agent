from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    agent_name: str = "First Agent"
    entert2_path: str = "/Users/auser/Downloads/entert2"
    feedback_store_path: str = "/Users/auser/Projects/ml-agent/first-agent/.first_agent_feedback.json"
    last_generation_path: str = "/Users/auser/Projects/ml-agent/first-agent/.first_agent_last_generation.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
