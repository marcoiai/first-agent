use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct ListingContext {
    pub title: String,
    pub category: String,
    pub price: f64,
    pub cost: f64,
    pub available_stock: u32,
    #[serde(default)]
    pub competitor_prices: Vec<f64>,
    #[serde(default)]
    pub views_last_7d: u32,
    #[serde(default)]
    pub sales_last_30d: u32,
    #[serde(default)]
    pub conversion_rate: f64,
}

#[derive(Debug, Deserialize)]
pub struct PricingRecommendationRequest {
    pub listing: ListingContext,
    #[serde(default = "default_margin")]
    pub min_margin_percent: f64,
    #[serde(default = "default_position")]
    pub target_position: String,
}

#[derive(Debug, Serialize)]
pub struct PricingRecommendation {
    pub recommended_price: f64,
    pub expected_margin_percent: f64,
    pub confidence: f64,
    pub rationale: Vec<String>,
    pub source: String,
}

fn default_margin() -> f64 {
    10.0
}

fn default_position() -> String {
    "competitive".to_string()
}

pub fn recommend_price(request: PricingRecommendationRequest) -> PricingRecommendation {
    let listing = request.listing;
    let market_anchor = if listing.competitor_prices.is_empty() {
        listing.price
    } else {
        listing.competitor_prices.iter().sum::<f64>() / listing.competitor_prices.len() as f64
    };

    let demand_bonus = if listing.views_last_7d > 200 && listing.conversion_rate > 0.03 {
        1.02
    } else {
        1.0
    };

    let positioning_factor = match request.target_position.as_str() {
        "aggressive" => 0.97,
        "premium" => 1.03,
        _ => 0.995,
    };

    let margin_floor = listing.cost * (1.0 + request.min_margin_percent / 100.0);
    let stock_pressure = if listing.available_stock < 5 { 1.015 } else { 1.0 };
    let suggested = (market_anchor * demand_bonus * positioning_factor * stock_pressure)
        .max(margin_floor);
    let margin = ((suggested - listing.cost) / suggested) * 100.0;

    PricingRecommendation {
        recommended_price: (suggested * 100.0).round() / 100.0,
        expected_margin_percent: (margin * 100.0).round() / 100.0,
        confidence: 0.71,
        rationale: vec![
            format!("Anchored recommendation on market price {:.2}.", market_anchor),
            format!(
                "Protected minimum requested margin of {:.2}%.",
                request.min_margin_percent
            ),
            "Adjusted for demand and stock pressure.".to_string(),
            format!(
                "Listing '{}' in category '{}' was considered.",
                listing.title, listing.category
            ),
        ],
        source: "rust-worker".to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::{ListingContext, PricingRecommendationRequest, recommend_price};

    #[test]
    fn respects_margin_floor() {
        let request = PricingRecommendationRequest {
            listing: ListingContext {
                title: "Mouse Gamer".to_string(),
                category: "peripherals".to_string(),
                price: 110.0,
                cost: 100.0,
                available_stock: 10,
                competitor_prices: vec![102.0, 105.0],
                views_last_7d: 50,
                sales_last_30d: 5,
                conversion_rate: 0.02,
            },
            min_margin_percent: 20.0,
            target_position: "competitive".to_string(),
        };

        let result = recommend_price(request);
        assert!(result.recommended_price >= 120.0);
    }
}
