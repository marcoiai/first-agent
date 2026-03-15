from typing import Any

from pydantic import BaseModel, Field


class ListingContext(BaseModel):
    marketplace: str = "mercadolivre"
    listing_id: str | None = None
    title: str
    category: str
    price: float = Field(gt=0)
    cost: float = Field(ge=0)
    available_stock: int = Field(ge=0)
    competitor_prices: list[float] = Field(default_factory=list)
    views_last_7d: int = Field(default=0, ge=0)
    sales_last_30d: int = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0.0, ge=0.0)
    attributes: dict[str, Any] = Field(default_factory=dict)


class PricingRecommendationRequest(BaseModel):
    listing: ListingContext
    min_margin_percent: float = Field(default=10.0, ge=0.0)
    target_position: str = Field(default="competitive")


class PricingRecommendation(BaseModel):
    recommended_price: float
    expected_margin_percent: float
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: list[str]
    source: str


class ListingDecisionRequest(BaseModel):
    listing: ListingContext
    business_goal: str = "maximize_profit_and_engagement"


class ListingDecisionResponse(BaseModel):
    summary: str
    actions: list[str]
    risks: list[str]
    pricing: PricingRecommendation
    source: str


class BuyerQuestionRequest(BaseModel):
    listing: ListingContext
    buyer_question: str = Field(min_length=3)
    tone: str = "helpful"


class BuyerQuestionResponse(BaseModel):
    reply: str
    follow_up_actions: list[str]
    source: str


class HealthResponse(BaseModel):
    status: str
    database: str
    openai_configured: bool


class ListingWorkflowRequest(BaseModel):
    marketplace: str = "mercadolivre"
    listing_id: str
    cost: float = Field(ge=0)
    competitor_prices: list[float] = Field(default_factory=list)
    views_last_7d: int = Field(default=0, ge=0)
    sales_last_30d: int = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0.0, ge=0.0)
    business_goal: str = "maximize_profit_and_engagement"


class ListingWorkflowResponse(BaseModel):
    listing: ListingContext
    evaluation: ListingDecisionResponse


class DirectListingWorkflowRequest(BaseModel):
    listing: ListingContext
    business_goal: str = "maximize_profit_and_engagement"


class SellerSyncRequest(BaseModel):
    marketplace: str = "mercadolivre"
    seller_id: str | None = None
    cost: float = Field(ge=0)
    competitor_prices: list[float] = Field(default_factory=list)
    views_last_7d: int = Field(default=0, ge=0)
    sales_last_30d: int = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0.0, ge=0.0)
    business_goal: str = "maximize_profit_and_engagement"
    limit: int = Field(default=10, ge=1, le=100)


class SellerSyncResponse(BaseModel):
    marketplace: str
    seller_id: str | None = None
    synced_count: int
    results: list[ListingWorkflowResponse]


class WebhookAckResponse(BaseModel):
    status: str
    provider: str
