import json
import shutil
from asyncio import create_subprocess_exec, subprocess
from pathlib import Path

from sqlalchemy.orm import Session

from config import get_settings
from repositories import ListingRepository
from schemas import PricingRecommendation, PricingRecommendationRequest


class PricingService:
    async def recommend_price(
        self,
        payload: PricingRecommendationRequest,
        session: Session | None = None,
        listing_snapshot_id: str | None = None,
    ) -> PricingRecommendation:
        worker_response = await self._run_worker(payload)
        recommendation = worker_response or self._fallback_pricing(payload)
        if session is not None:
            repository = ListingRepository(session)
            snapshot_id = listing_snapshot_id
            if snapshot_id is None:
                snapshot = repository.create_snapshot(payload.listing)
                snapshot_id = snapshot.id
            repository.log_pricing_decision(snapshot_id, payload, recommendation)
            session.commit()
        return recommendation

    async def _run_worker(
        self,
        payload: PricingRecommendationRequest,
    ) -> PricingRecommendation | None:
        settings = get_settings()
        configured_worker = Path(settings.pricing_worker_bin)
        worker_path = shutil.which("pricing_worker") or str(configured_worker.resolve())
        if worker_path is None:
            return None

        try:
            process = await create_subprocess_exec(
                worker_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            return None
        stdout, stderr = await process.communicate(
            json.dumps(payload.model_dump()).encode("utf-8")
        )
        if process.returncode != 0 or not stdout:
            if stderr:
                print(stderr.decode("utf-8"))
            return None
        return PricingRecommendation.model_validate_json(stdout.decode("utf-8"))

    def _fallback_pricing(
        self,
        payload: PricingRecommendationRequest,
    ) -> PricingRecommendation:
        listing = payload.listing
        market_anchor = (
            sum(listing.competitor_prices) / len(listing.competitor_prices)
            if listing.competitor_prices
            else listing.price
        )
        min_allowed_price = listing.cost * (1 + payload.min_margin_percent / 100)
        recommended_price = max(min_allowed_price, market_anchor * 0.99)
        expected_margin = ((recommended_price - listing.cost) / recommended_price) * 100
        return PricingRecommendation(
            recommended_price=round(recommended_price, 2),
            expected_margin_percent=round(expected_margin, 2),
            confidence=0.52,
            rationale=[
                "Fallback heuristic used because the Rust pricing worker was unavailable.",
                "Targeted a slightly competitive price versus the observed market anchor.",
                "Protected the requested minimum margin floor.",
            ],
            source="python-fallback",
        )
