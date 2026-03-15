from services.marketplace_adapter import MarketplaceAdapter
from services.marketplace_adapters.fake import FakeMarketplaceAdapter
from services.marketplace_adapters.mercadolivre import MercadoLivreAdapter
from services.marketplace_adapters.shopee import ShopeeAdapter


def get_marketplace_adapter(marketplace: str) -> MarketplaceAdapter:
    normalized = marketplace.strip().lower()
    adapters: dict[str, MarketplaceAdapter] = {
        "mercadolivre": MercadoLivreAdapter(),
        "mercado_livre": MercadoLivreAdapter(),
        "meli": MercadoLivreAdapter(),
        "fake": FakeMarketplaceAdapter(),
        "mock": FakeMarketplaceAdapter(),
        "demo": FakeMarketplaceAdapter(),
        "shopee": ShopeeAdapter(),
    }
    try:
        return adapters[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported marketplace '{marketplace}'.") from exc
