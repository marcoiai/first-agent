from sqlalchemy.orm import Session

from models import BuyerQuestionLog, ListingEvaluation, ListingSnapshot, PricingDecision
from schemas import (
    BuyerQuestionRequest,
    BuyerQuestionResponse,
    ListingContext,
    ListingDecisionRequest,
    ListingDecisionResponse,
    PricingRecommendation,
    PricingRecommendationRequest,
)


class ListingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_snapshot(self, listing: ListingContext) -> ListingSnapshot:
        snapshot = ListingSnapshot(
            marketplace=listing.marketplace,
            external_listing_id=listing.listing_id,
            title=listing.title,
            category=listing.category,
            current_price=listing.price,
            cost=listing.cost,
            available_stock=listing.available_stock,
            competitor_prices=listing.competitor_prices,
            views_last_7d=listing.views_last_7d,
            sales_last_30d=listing.sales_last_30d,
            conversion_rate=listing.conversion_rate,
            attributes=listing.attributes,
        )
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def log_pricing_decision(
        self,
        snapshot_id: str,
        request: PricingRecommendationRequest,
        recommendation: PricingRecommendation,
    ) -> PricingDecision:
        decision = PricingDecision(
            listing_snapshot_id=snapshot_id,
            min_margin_percent=request.min_margin_percent,
            target_position=request.target_position,
            recommended_price=recommendation.recommended_price,
            expected_margin_percent=recommendation.expected_margin_percent,
            confidence=recommendation.confidence,
            source=recommendation.source,
            rationale=recommendation.rationale,
        )
        self.session.add(decision)
        self.session.flush()
        return decision

    def log_listing_evaluation(
        self,
        snapshot_id: str,
        request: ListingDecisionRequest,
        response: ListingDecisionResponse,
    ) -> ListingEvaluation:
        evaluation = ListingEvaluation(
            listing_snapshot_id=snapshot_id,
            business_goal=request.business_goal,
            summary=response.summary,
            actions=response.actions,
            risks=response.risks,
            pricing_source=response.pricing.source,
            source=response.source,
        )
        self.session.add(evaluation)
        self.session.flush()
        return evaluation

    def log_buyer_question(
        self,
        snapshot_id: str,
        request: BuyerQuestionRequest,
        response: BuyerQuestionResponse,
    ) -> BuyerQuestionLog:
        question_log = BuyerQuestionLog(
            listing_snapshot_id=snapshot_id,
            buyer_question=request.buyer_question,
            tone=request.tone,
            reply=response.reply,
            follow_up_actions=response.follow_up_actions,
            source=response.source,
        )
        self.session.add(question_log)
        self.session.flush()
        return question_log
