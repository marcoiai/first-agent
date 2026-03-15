import argparse
import asyncio
import json

from db import SessionLocal
from schemas import DirectListingWorkflowRequest, ListingContext
from services.operator_service import OperatorService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a normalized listing payload without marketplace auth.",
    )
    parser.add_argument("--marketplace", default="manual")
    parser.add_argument("--listing-id", default=None)
    parser.add_argument("--title", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--price", required=True, type=float)
    parser.add_argument("--cost", required=True, type=float)
    parser.add_argument("--available-stock", required=True, type=int)
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
        "--attribute",
        action="append",
        default=[],
        help="Listing attribute in key=value form. Can be passed multiple times.",
    )
    parser.add_argument(
        "--business-goal",
        default="maximize_profit_and_engagement",
    )
    return parser.parse_args()


def parse_attributes(raw_attributes: list[str]) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for entry in raw_attributes:
        if "=" not in entry:
            raise ValueError(f"Invalid attribute '{entry}'. Use key=value.")
        key, value = entry.split("=", 1)
        attributes[key] = value
    return attributes


async def main() -> None:
    args = parse_args()
    listing = ListingContext(
        marketplace=args.marketplace,
        listing_id=args.listing_id,
        title=args.title,
        category=args.category,
        price=args.price,
        cost=args.cost,
        available_stock=args.available_stock,
        competitor_prices=args.competitor_price,
        views_last_7d=args.views_last_7d,
        sales_last_30d=args.sales_last_30d,
        conversion_rate=args.conversion_rate,
        attributes=parse_attributes(args.attribute),
    )
    payload = DirectListingWorkflowRequest(
        listing=listing,
        business_goal=args.business_goal,
    )
    session = SessionLocal()
    try:
        result = await OperatorService().evaluate_direct_listing(payload, session)
    finally:
        session.close()

    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
