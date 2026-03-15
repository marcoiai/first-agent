from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db_session
from schemas import BuyerQuestionRequest, BuyerQuestionResponse
from services.question_service import QuestionService


router = APIRouter(prefix="/questions", tags=["questions"])
service = QuestionService()


@router.post("/reply", response_model=BuyerQuestionResponse)
async def reply_to_question(
    payload: BuyerQuestionRequest,
    session: Session = Depends(get_db_session),
) -> BuyerQuestionResponse:
    return await service.answer_buyer(payload, session=session)
