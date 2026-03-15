from typing import Any

from schemas import ListingContext, ListingWorkflowRequest
from services.marketplace_adapter import MarketplaceAdapter


class ShopeeAdapter(MarketplaceAdapter):
    marketplace_name = "shopee"

    async def get_listing(self, listing_id: str) -> dict[str, Any]:
        raise NotImplementedError(
            "Shopee integration is not implemented yet. Add authenticated Shopee API calls here."
        )

    async def list_seller_listing_ids(
        self,
        seller_id: str | None = None,
        limit: int = 20,
    ) -> list[str]:
        raise NotImplementedError(
            "Shopee seller listing sync is not implemented yet. Add authenticated Shopee API calls here."
        )

    def to_listing_context(
        self,
        item: dict[str, Any],
        payload: ListingWorkflowRequest,
    ) -> ListingContext:
        return ListingContext(
            marketplace=self.marketplace_name,
            listing_id=str(item.get("item_id") or payload.listing_id),
            title=item.get("item_name") or "Untitled listing",
            category=str(item.get("category_id") or "unknown"),
            price=float(item.get("price_info", {}).get("current_price") or 0),
            cost=payload.cost,
            available_stock=int(item.get("stock_info", {}).get("seller_stock", 0)),
            competitor_prices=payload.competitor_prices,
            views_last_7d=payload.views_last_7d,
            sales_last_30d=payload.sales_last_30d,
            conversion_rate=payload.conversion_rate,
            attributes=item,
        )
