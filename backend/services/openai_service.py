from openai import AsyncOpenAI

from config import get_settings


def is_openai_configured() -> bool:
    return bool(get_settings().openai_api_key)


def get_openai_client() -> AsyncOpenAI | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    return AsyncOpenAI(api_key=settings.openai_api_key)
