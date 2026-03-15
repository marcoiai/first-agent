use std::io::{self, Read};

use pricing_worker::{PricingRecommendationRequest, recommend_price};

fn main() {
    let mut buffer = String::new();
    io::stdin()
        .read_to_string(&mut buffer)
        .expect("failed to read stdin");

    let request: PricingRecommendationRequest =
        serde_json::from_str(&buffer).expect("invalid request json");
    let response = recommend_price(request);
    println!(
        "{}",
        serde_json::to_string(&response).expect("failed to serialize response")
    );
}
