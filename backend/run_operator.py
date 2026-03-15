import argparse
import asyncio
import json

from db import SessionLocal
from schemas import ListingWorkflowRequest
from services.operator_service import OperatorService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a marketplace listing, evaluate it, and persist the result.",
    )
    parser.add_argument("--listing-id", required=True, help="Marketplace listing ID, e.g. MLB123 or DEMO-001")
    parser.add_argument(
        "--marketplace",
        default="mercadolivre",
        help="Marketplace adapter to use, e.g. mercadolivre, fake, or shopee",
    )
    parser.add_argument("--cost", required=True, type=float, help="Your unit cost for the item")
    parser.add_argument(
        "--competitor-price",
        action="append",
        type=float,
        default=[],
        help="Observed competitor price. Can be passed multiple times.",
    )
    parser.add_argument("--views-last-7d", type=int, default=0)
    parser.add_argument("--sales-last-30d", type=int, default=0)
    parser.add_argument("--conversion-rate", type=float, default=0.0)
    parser.add_argument(
        "--business-goal",
        default="maximize_profit_and_engagement",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    payload = ListingWorkflowRequest(
        marketplace=args.marketplace,
        listing_id=args.listing_id,
        cost=args.cost,
        competitor_prices=args.competitor_price,
        views_last_7d=args.views_last_7d,
        sales_last_30d=args.sales_last_30d,
        conversion_rate=args.conversion_rate,
        business_goal=args.business_goal,
    )
    session = SessionLocal()
    try:
        result = await OperatorService().evaluate_listing_from_marketplace(payload, session)
    finally:
        session.close()

    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
