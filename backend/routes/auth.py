from fastapi import APIRouter, Query
from pydantic import BaseModel

from services.mercadolivre_auth_service import MercadoLivreAuthService


class MercadoLivreAuthorizationUrlResponse(BaseModel):
    authorization_url: str


class MercadoLivreTokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    scope: str | None = None
    user_id: int | None = None


router = APIRouter(prefix="/auth", tags=["auth"])
service = MercadoLivreAuthService()


@router.get("/mercadolivre/url", response_model=MercadoLivreAuthorizationUrlResponse)
async def mercadolivre_authorization_url(
    state: str | None = Query(default=None),
) -> MercadoLivreAuthorizationUrlResponse:
    return MercadoLivreAuthorizationUrlResponse(
        authorization_url=service.build_authorization_url(state=state),
    )


@router.get("/mercadolivre/callback", response_model=MercadoLivreTokenResponse)
async def mercadolivre_callback(
    code: str = Query(...),
) -> MercadoLivreTokenResponse:
    token_data = await service.exchange_code(code)
    return MercadoLivreTokenResponse.model_validate(token_data)
