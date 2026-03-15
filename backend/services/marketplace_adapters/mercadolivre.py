from typing import Any

import httpx
from fastapi import HTTPException

from config import get_settings
from schemas import ListingContext, ListingWorkflowRequest
from services.marketplace_adapter import MarketplaceAdapter


class MercadoLivreAdapter(MarketplaceAdapter):
    marketplace_name = "mercadolivre"

    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "ml-agent/0.1",
        }
        if self.settings.mercadolivre_access_token:
            headers["Authorization"] = f"Bearer {self.settings.mercadolivre_access_token}"
        return headers

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        path: str,
    ) -> dict[str, Any] | None:
        try:
            response = await client.get(path)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            detail = exc.response.text or str(exc)
            raise HTTPException(
                status_code=502,
                detail=f"Mercado Livre API error for '{path}': {detail}",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Mercado Livre API request failed for '{path}': {exc}",
            ) from exc

    async def get_listing(self, listing_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=self.settings.mercadolivre_api_base,
            timeout=self.settings.request_timeout_seconds,
            headers=self._headers(),
        ) as client:
            item = await self._get_json(client, f"/items/{listing_id}")
            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Mercado Livre listing '{listing_id}' was not found.",
                )

            description = await self._get_json(client, f"/items/{listing_id}/description")
            if description and description.get("plain_text"):
                item["description_plain_text"] = description["plain_text"]
            return item

    async def list_seller_listing_ids(
        self,
        seller_id: str | None = None,
        limit: int = 20,
    ) -> list[str]:
        async with httpx.AsyncClient(
            base_url=self.settings.mercadolivre_api_base,
            timeout=self.settings.request_timeout_seconds,
            headers=self._headers(),
        ) as client:
            resolved_seller_id = seller_id
            if resolved_seller_id is None:
                me = await self._get_json(client, "/users/me")
                if me is None or not me.get("id"):
                    raise HTTPException(
                        status_code=502,
                        detail="Mercado Livre API did not return the authenticated seller id.",
                    )
                resolved_seller_id = str(me["id"])

            search = await self._get_json(
                client,
                f"/users/{resolved_seller_id}/items/search?limit={max(limit, 1)}",
            )
            if search is None:
                return []
            results = search.get("results", [])
            return [str(item_id) for item_id in results[:limit]]

    def _resolve_available_stock(self, item: dict[str, Any]) -> int:
        available_quantity = item.get("available_quantity")
        if available_quantity is not None:
            return max(int(available_quantity), 0)

        variation_stock = 0
        for variation in item.get("variations", []):
            quantity = variation.get("available_quantity")
            if quantity is not None:
                variation_stock += int(quantity)
        if variation_stock > 0:
            return max(variation_stock, 0)

        initial_quantity = item.get("initial_quantity", 0)
        return max(int(initial_quantity or 0), 0)

    def _collect_attributes(self, item: dict[str, Any]) -> dict[str, Any]:
        attributes: dict[str, Any] = {
            "condition": item.get("condition"),
            "listing_type_id": item.get("listing_type_id"),
            "permalink": item.get("permalink"),
            "status": item.get("status"),
            "thumbnail": item.get("thumbnail"),
            "secure_thumbnail": item.get("secure_thumbnail"),
            "catalog_product_id": item.get("catalog_product_id"),
            "domain_id": item.get("domain_id"),
            "accepts_mercadopago": item.get("accepts_mercadopago"),
            "buying_mode": item.get("buying_mode"),
            "shipping": item.get("shipping", {}),
            "seller_address": item.get("seller_address", {}),
            "seller_id": item.get("seller_id"),
            "warranty": item.get("warranty"),
            "health": item.get("health"),
            "description_plain_text": item.get("description_plain_text"),
            "pictures": item.get("pictures", []),
            "tags": item.get("tags", []),
        }

        for attribute in item.get("attributes", []):
            name = attribute.get("id") or attribute.get("name")
            value = attribute.get("value_name") or attribute.get("value_id")
            if name and value is not None:
                attributes[str(name).lower()] = value

        return {key: value for key, value in attributes.items() if value not in (None, "", [], {})}

    def to_listing_context(
        self,
        item: dict[str, Any],
        payload: ListingWorkflowRequest,
    ) -> ListingContext:
        category = item.get("category_id") or "unknown"
        title = item.get("title") or "Untitled listing"
        price = float(item.get("price") or 0)

        return ListingContext(
            marketplace=self.marketplace_name,
            listing_id=item.get("id"),
            title=title,
            category=category,
            price=price,
            cost=payload.cost,
            available_stock=self._resolve_available_stock(item),
            competitor_prices=payload.competitor_prices,
            views_last_7d=payload.views_last_7d,
            sales_last_30d=payload.sales_last_30d,
            conversion_rate=payload.conversion_rate,
            attributes=self._collect_attributes(item),
        )
