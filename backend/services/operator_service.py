from fastapi import HTTPException
from sqlalchemy.orm import Session

from schemas import (
    DirectListingWorkflowRequest,
    ListingDecisionRequest,
    SellerSyncRequest,
    SellerSyncResponse,
    ListingWorkflowRequest,
    ListingWorkflowResponse,
)
from services.agent_service import AgentService
from services.marketplace_registry import get_marketplace_adapter


class OperatorService:
    def __init__(self) -> None:
        self.agent_service = AgentService()

    async def evaluate_listing_from_marketplace(
        self,
        payload: ListingWorkflowRequest,
        session: Session,
    ) -> ListingWorkflowResponse:
        try:
            adapter = get_marketplace_adapter(payload.marketplace)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        try:
            item = await adapter.get_listing(payload.listing_id)
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc

        listing = adapter.to_listing_context(item, payload)
        evaluation = await self.agent_service.evaluate_listing(
            ListingDecisionRequest(
                listing=listing,
                business_goal=payload.business_goal,
            ),
            session=session,
        )
        return ListingWorkflowResponse(listing=listing, evaluation=evaluation)

    async def evaluate_direct_listing(
        self,
        payload: DirectListingWorkflowRequest,
        session: Session,
    ) -> ListingWorkflowResponse:
        evaluation = await self.agent_service.evaluate_listing(
            ListingDecisionRequest(
                listing=payload.listing,
                business_goal=payload.business_goal,
            ),
            session=session,
        )
        return ListingWorkflowResponse(listing=payload.listing, evaluation=evaluation)

    async def sync_seller_listings(
        self,
        payload: SellerSyncRequest,
        session: Session,
    ) -> SellerSyncResponse:
        try:
            adapter = get_marketplace_adapter(payload.marketplace)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        try:
            listing_ids = await adapter.list_seller_listing_ids(
                seller_id=payload.seller_id,
                limit=payload.limit,
            )
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc

        results: list[ListingWorkflowResponse] = []
        for listing_id in listing_ids:
            result = await self.evaluate_listing_from_marketplace(
                ListingWorkflowRequest(
                    marketplace=payload.marketplace,
                    listing_id=listing_id,
                    cost=payload.cost,
                    competitor_prices=payload.competitor_prices,
                    views_last_7d=payload.views_last_7d,
                    sales_last_30d=payload.sales_last_30d,
                    conversion_rate=payload.conversion_rate,
                    business_goal=payload.business_goal,
                ),
                session=session,
            )
            results.append(result)

        return SellerSyncResponse(
            marketplace=payload.marketplace,
            seller_id=payload.seller_id,
            synced_count=len(results),
            results=results,
        )
