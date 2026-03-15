from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from schemas import ListingContext, ListingWorkflowRequest


class MarketplaceAdapter(ABC):
    marketplace_name: str

    @abstractmethod
    async def get_listing(self, listing_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def list_seller_listing_ids(
        self,
        seller_id: str | None = None,
        limit: int = 20,
    ) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def to_listing_context(
        self,
        item: dict[str, Any],
        payload: ListingWorkflowRequest,
    ) -> ListingContext:
        raise NotImplementedError
