from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

from config import get_settings


class MercadoLivreAuthService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _require_oauth_config(self) -> None:
        missing = []
        if not self.settings.mercadolivre_app_id:
            missing.append("MERCADOLIVRE_APP_ID")
        if not self.settings.mercadolivre_client_secret:
            missing.append("MERCADOLIVRE_CLIENT_SECRET")
        if not self.settings.mercadolivre_redirect_uri:
            missing.append("MERCADOLIVRE_REDIRECT_URI")
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing Mercado Livre OAuth config: {', '.join(missing)}",
            )

    def build_authorization_url(self, state: str | None = None) -> str:
        self._require_oauth_config()
        params = {
            "response_type": "code",
            "client_id": self.settings.mercadolivre_app_id,
            "redirect_uri": self.settings.mercadolivre_redirect_uri,
        }
        if state:
            params["state"] = state
        return f"{self.settings.mercadolivre_auth_base}/authorization?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        self._require_oauth_config()
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.settings.mercadolivre_app_id,
            "client_secret": self.settings.mercadolivre_client_secret,
            "code": code,
            "redirect_uri": self.settings.mercadolivre_redirect_uri,
        }
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self.settings.mercadolivre_api_base}/oauth/token",
                    json=payload,
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text or str(exc)
                raise HTTPException(
                    status_code=502,
                    detail=f"Mercado Livre token exchange failed: {detail}",
                ) from exc
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=f"Mercado Livre token exchange request failed: {exc}",
                ) from exc
        return response.json()
