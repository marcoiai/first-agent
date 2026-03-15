from fastapi import APIRouter

from db import check_database_health
from schemas import HealthResponse
from services.openai_service import is_openai_configured


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    db_ok, db_message = check_database_health()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database=db_message if not db_ok else "ok",
        openai_configured=is_openai_configured(),
    )
