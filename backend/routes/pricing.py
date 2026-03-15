from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from db import get_db_session
from schemas import PricingRecommendation, PricingRecommendationRequest
from services.pricing_service import PricingService


router = APIRouter(prefix="/pricing", tags=["pricing"])
service = PricingService()


@router.post("/recommendation", response_model=PricingRecommendation)
async def pricing_recommendation(
    payload: PricingRecommendationRequest,
    session: Session = Depends(get_db_session),
) -> PricingRecommendation:
    return await service.recommend_price(payload, session=session)
