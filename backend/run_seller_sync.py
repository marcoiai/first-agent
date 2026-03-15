import argparse
import asyncio
import json

from db import SessionLocal
from schemas import SellerSyncRequest
from services.operator_service import OperatorService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync and evaluate multiple seller listings from a marketplace adapter.",
    )
    parser.add_argument(
        "--marketplace",
        default="mercadolivre",
        help="Marketplace adapter to use, e.g. mercadolivre or fake",
    )
    parser.add_argument("--seller-id", default=None, help="Seller id; omit to use the authenticated account when supported.")
    parser.add_argument("--cost", required=True, type=float, help="Default unit cost to apply during sync.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of listings to sync.")
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
    parser.add_argument("--business-goal", default="maximize_profit_and_engagement")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    payload = SellerSyncRequest(
        marketplace=args.marketplace,
        seller_id=args.seller_id,
        cost=args.cost,
        limit=args.limit,
        competitor_prices=args.competitor_price,
        views_last_7d=args.views_last_7d,
        sales_last_30d=args.sales_last_30d,
        conversion_rate=args.conversion_rate,
        business_goal=args.business_goal,
    )
    session = SessionLocal()
    try:
        result = await OperatorService().sync_seller_listings(payload, session)
    finally:
        session.close()

    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
