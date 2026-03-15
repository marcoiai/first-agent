from pathlib import Path

from sqlalchemy.orm import Session

from config import get_settings
from repositories import ListingRepository
from schemas import (
    ListingDecisionRequest,
    ListingDecisionResponse,
    PricingRecommendationRequest,
)
from services.openai_service import get_openai_client
from services.pricing_service import PricingService


class AgentService:
    def __init__(self) -> None:
        self.pricing_service = PricingService()
        self.prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "listing_strategy.txt"

    async def evaluate_listing(
        self,
        payload: ListingDecisionRequest,
        session: Session | None = None,
    ) -> ListingDecisionResponse:
        repository = ListingRepository(session) if session is not None else None
        snapshot = repository.create_snapshot(payload.listing) if repository is not None else None
        pricing = await self.pricing_service.recommend_price(
            PricingRecommendationRequest(listing=payload.listing),
            session=session,
            listing_snapshot_id=snapshot.id if snapshot is not None else None,
        )
        client = get_openai_client()
        if client is None:
            response = self._fallback_response(payload, pricing)
            if repository is not None and snapshot is not None:
                repository.log_listing_evaluation(snapshot.id, payload, response)
                session.commit()
            return response

        prompt = self.prompt_path.read_text(encoding="utf-8")
        settings = get_settings()
        response = await client.responses.create(
            model=settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": (
                        "Generate listing actions, risks, and a concise summary for this "
                        f"Mercado Livre listing: {payload.model_dump_json(indent=2)} "
                        f"Pricing recommendation: {pricing.model_dump_json(indent=2)}"
                    ),
                },
            ],
        )
        text = response.output_text
        result = ListingDecisionResponse(
            summary=text.strip(),
            actions=[
                "Apply the recommended price and monitor 24-hour conversion shifts.",
                "Refresh the title and key attributes to strengthen search relevance.",
            ],
            risks=[
                "Model response should be reviewed before any fully automated listing update.",
            ],
            pricing=pricing,
            source="openai",
        )
        if repository is not None and snapshot is not None:
            repository.log_listing_evaluation(snapshot.id, payload, result)
            session.commit()
        return result

    def _fallback_response(
        self,
        payload: ListingDecisionRequest,
        pricing,
    ) -> ListingDecisionResponse:
        listing = payload.listing
        slow_sales = listing.views_last_7d > 0 and listing.sales_last_30d == 0
        actions = [
            f"Set the listing price near {pricing.recommended_price} to balance profit and competitiveness.",
            "Lead the title with product type, brand, and strongest differentiator.",
            "Ensure shipping, warranty, and return conditions are explicit in the description.",
        ]
        if slow_sales:
            actions.append("Test a stronger hero image or bundle offer to improve click-through.")

        risks = [
            "Competitor pricing may shift quickly in fast-moving categories.",
            "Low-stock listings should avoid overly aggressive discounting.",
        ]

        summary = (
            f"The listing for '{listing.title}' should stay competitive without crossing the "
            f"margin floor. Recommended price is {pricing.recommended_price}, with focus on "
            "better relevance and buyer trust signals."
        )
        return ListingDecisionResponse(
            summary=summary,
            actions=actions,
            risks=risks,
            pricing=pricing,
            source="heuristic",
        )
