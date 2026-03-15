import json
import logging
from typing import Any

from fastapi import APIRouter, Request

from schemas import WebhookAckResponse


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/mercadolivre", response_model=WebhookAckResponse)
async def mercadolivre_webhook_challenge(request: Request) -> WebhookAckResponse:
    query_params = dict(request.query_params)
    logger.info("Mercado Livre webhook GET received: %s", json.dumps(query_params))
    return WebhookAckResponse(status="ok", provider="mercadolivre")


@router.post("/mercadolivre", response_model=WebhookAckResponse)
async def mercadolivre_webhook(request: Request) -> WebhookAckResponse:
    try:
        payload: Any = await request.json()
    except Exception:
        payload = {"raw_body": (await request.body()).decode("utf-8", errors="ignore")}
    logger.info("Mercado Livre webhook POST received: %s", json.dumps(payload))
    return WebhookAckResponse(status="ok", provider="mercadolivre")
