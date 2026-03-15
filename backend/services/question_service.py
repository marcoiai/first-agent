from pathlib import Path

from sqlalchemy.orm import Session

from config import get_settings
from repositories import ListingRepository
from schemas import BuyerQuestionRequest, BuyerQuestionResponse
from services.openai_service import get_openai_client


class QuestionService:
    def __init__(self) -> None:
        self.prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "buyer_reply.txt"

    async def answer_buyer(
        self,
        payload: BuyerQuestionRequest,
        session: Session | None = None,
    ) -> BuyerQuestionResponse:
        repository = ListingRepository(session) if session is not None else None
        snapshot = repository.create_snapshot(payload.listing) if repository is not None else None
        client = get_openai_client()
        if client is None:
            response = self._fallback_response(payload)
            if repository is not None and snapshot is not None:
                repository.log_buyer_question(snapshot.id, payload, response)
                session.commit()
            return response

        prompt = self.prompt_path.read_text(encoding="utf-8")
        settings = get_settings()
        response = await client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"Listing context: {payload.listing.model_dump_json(indent=2)}\n"
                        f"Buyer question: {payload.buyer_question}\n"
                        f"Tone: {payload.tone}"
                    ),
                },
            ],
        )
        result = BuyerQuestionResponse(
            reply=response.output_text.strip(),
            follow_up_actions=[
                "Log recurring buyer objections to improve listing copy.",
            ],
            source="openai",
        )
        if repository is not None and snapshot is not None:
            repository.log_buyer_question(snapshot.id, payload, result)
            session.commit()
        return result

    def _fallback_response(self, payload: BuyerQuestionRequest) -> BuyerQuestionResponse:
        return BuyerQuestionResponse(
            reply=(
                f"Oi! Sobre '{payload.listing.title}': {payload.buyer_question.strip()} "
                "Posso confirmar os detalhes do anuncio e ajudar com envio, garantia e prazo."
            ),
            follow_up_actions=[
                "Review whether this question reveals missing information in the listing.",
            ],
            source="heuristic",
        )
