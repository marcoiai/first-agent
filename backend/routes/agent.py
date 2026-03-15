from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db_session
from schemas import ListingDecisionRequest, ListingDecisionResponse
from services.agent_service import AgentService


router = APIRouter(prefix="/agent", tags=["agent"])
service = AgentService()


@router.post("/evaluate-listing", response_model=ListingDecisionResponse)
async def evaluate_listing(
    payload: ListingDecisionRequest,
    session: Session = Depends(get_db_session),
) -> ListingDecisionResponse:
    return await service.evaluate_listing(payload, session=session)
