from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db_session
from schemas import (
    DirectListingWorkflowRequest,
    SellerSyncRequest,
    SellerSyncResponse,
    ListingWorkflowRequest,
    ListingWorkflowResponse,
)
from services.operator_service import OperatorService


router = APIRouter(prefix="/operations", tags=["operations"])
service = OperatorService()


@router.post("/evaluate-marketplace-listing", response_model=ListingWorkflowResponse)
async def evaluate_marketplace_listing(
    payload: ListingWorkflowRequest,
    session: Session = Depends(get_db_session),
) -> ListingWorkflowResponse:
    return await service.evaluate_listing_from_marketplace(payload, session)


@router.post("/evaluate-direct-listing", response_model=ListingWorkflowResponse)
async def evaluate_direct_listing(
    payload: DirectListingWorkflowRequest,
    session: Session = Depends(get_db_session),
) -> ListingWorkflowResponse:
    return await service.evaluate_direct_listing(payload, session)


@router.post("/sync-seller-listings", response_model=SellerSyncResponse)
async def sync_seller_listings(
    payload: SellerSyncRequest,
    session: Session = Depends(get_db_session),
) -> SellerSyncResponse:
    return await service.sync_seller_listings(payload, session)
