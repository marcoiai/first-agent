from typing import Any

from schemas import ListingContext, ListingWorkflowRequest
from services.marketplace_adapter import MarketplaceAdapter


class FakeMarketplaceAdapter(MarketplaceAdapter):
    marketplace_name = "fake"

    async def get_listing(self, listing_id: str) -> dict[str, Any]:
        seed = sum(ord(char) for char in listing_id)
        price = round(80 + (seed % 120) + 0.9, 2)
        stock = 3 + (seed % 15)
        category = ["audio", "home", "gaming", "electronics"][seed % 4]

        return {
            "id": listing_id,
            "title": f"Demo Listing {listing_id}",
            "category": category,
            "price": price,
            "available_stock": stock,
            "attributes": {
                "brand": "DemoBrand",
                "condition": "new",
                "origin": "fake-adapter",
            },
            "engagement_hint": {
                "views_last_7d": 40 + (seed % 200),
                "sales_last_30d": 1 + (seed % 12),
            },
        }

    async def list_seller_listing_ids(
        self,
        seller_id: str | None = None,
        limit: int = 20,
    ) -> list[str]:
        prefix = (seller_id or "DEMO").upper()
        return [f"{prefix}-{index:03d}" for index in range(1, max(limit, 1) + 1)]

    def to_listing_context(
        self,
        item: dict[str, Any],
        payload: ListingWorkflowRequest,
    ) -> ListingContext:
        engagement_hint = item.get("engagement_hint", {})
        return ListingContext(
            marketplace=self.marketplace_name,
            listing_id=str(item.get("id") or payload.listing_id),
            title=item.get("title") or f"Demo Listing {payload.listing_id}",
            category=str(item.get("category") or "demo"),
            price=float(item.get("price") or 0),
            cost=payload.cost,
            available_stock=int(item.get("available_stock") or 0),
            competitor_prices=payload.competitor_prices,
            views_last_7d=payload.views_last_7d or int(engagement_hint.get("views_last_7d", 0)),
            sales_last_30d=payload.sales_last_30d or int(engagement_hint.get("sales_last_30d", 0)),
            conversion_rate=payload.conversion_rate,
            attributes=item.get("attributes", {}),
        )
