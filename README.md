# Marketplace AI Selling Agent

Baseline workspace for a profit-and-engagement optimization agent:

- FastAPI backend for listing decisions and buyer replies
- Rust pricing worker for deterministic pricing recommendations
- Postgres-ready config hooks
- OpenAI integration with safe fallbacks when credentials are missing

## Run the backend

```bash
cd backend
python3 -m uvicorn app:app --reload
```

## Run database migrations

```bash
cd backend
./venv/bin/alembic -c alembic.ini upgrade head
```

## Build the pricing worker

```bash
cd workers/pricing_worker
cargo build
```

## Main API routes

- `GET /auth/mercadolivre/url`
- `GET /auth/mercadolivre/callback`
- `GET /health`
- `GET /webhooks/mercadolivre`
- `POST /agent/evaluate-listing`
- `POST /operations/evaluate-direct-listing`
- `POST /operations/evaluate-marketplace-listing`
- `POST /operations/sync-seller-listings`
- `POST /pricing/recommendation`
- `POST /questions/reply`
- `POST /webhooks/mercadolivre`

## Persistence

The backend now stores:

- listing snapshots
- pricing decisions
- listing evaluations
- buyer question/reply logs

## Operator workflow

## Mercado Livre OAuth

Set these in `backend/.env`:

```env
MERCADOLIVRE_APP_ID=your_app_id
MERCADOLIVRE_CLIENT_SECRET=your_client_secret
MERCADOLIVRE_REDIRECT_URI=http://127.0.0.1:8000/auth/mercadolivre/callback
```

Start the backend and open:

```text
http://127.0.0.1:8000/auth/mercadolivre/url
```

That route returns the Mercado Livre authorization URL. After you authorize the app, the callback route exchanges the `code` for tokens and returns them as JSON.

## Mercado Livre notifications

For webhook/notification configuration, use:

```text
https://YOUR_DOMAIN/webhooks/mercadolivre
```

The current endpoint acknowledges the request and logs the payload so you can complete the provider setup before implementing specific event processing.

Evaluate a real marketplace listing by ID:

```bash
cd backend
./venv/bin/python run_operator.py \
  --marketplace mercadolivre \
  --listing-id MLB123456789 \
  --cost 120 \
  --competitor-price 189.9 \
  --competitor-price 194.9 \
  --views-last-7d 120 \
  --sales-last-30d 10 \
  --conversion-rate 0.05
```

Or use the API route:

```bash
curl -X POST http://127.0.0.1:8000/operations/evaluate-marketplace-listing \
  -H "Content-Type: application/json" \
  -d '{
    "marketplace": "mercadolivre",
    "listing_id": "MLB123456789",
    "cost": 120,
    "competitor_prices": [189.9, 194.9],
    "views_last_7d": 120,
    "sales_last_30d": 10,
    "conversion_rate": 0.05
  }'
```

## Marketplace adapters

- `mercadolivre`: implemented and ready to fetch listings
- `fake`: implemented for demos and architecture testing without auth
- `shopee`: scaffolded, but returns `501 Not Implemented` until its API integration is added

Use the fake adapter through the marketplace path:

```bash
cd backend
./venv/bin/python run_operator.py \
  --marketplace fake \
  --listing-id DEMO-001 \
  --cost 120 \
  --competitor-price 189.9 \
  --competitor-price 194.9
```

Sync multiple listings for a seller:

```bash
cd backend
./venv/bin/python run_seller_sync.py \
  --marketplace fake \
  --seller-id demo-seller \
  --cost 120 \
  --limit 3 \
  --competitor-price 189.9 \
  --competitor-price 194.9
```

## No-auth workflow

Evaluate a listing directly without any marketplace API:

```bash
cd backend
./venv/bin/python run_direct_operator.py \
  --marketplace manual \
  --listing-id TEST-001 \
  --title "Fone Bluetooth Sony" \
  --category audio \
  --price 199.9 \
  --cost 120 \
  --available-stock 8 \
  --competitor-price 189.9 \
  --competitor-price 194.9 \
  --views-last-7d 120 \
  --sales-last-30d 10 \
  --conversion-rate 0.05 \
  --attribute brand=Sony \
  --attribute condition=new
```

Or use the API route:

```bash
curl -X POST http://127.0.0.1:8000/operations/evaluate-direct-listing \
  -H "Content-Type: application/json" \
  -d '{
    "listing": {
      "marketplace": "manual",
      "listing_id": "TEST-001",
      "title": "Fone Bluetooth Sony",
      "category": "audio",
      "price": 199.9,
      "cost": 120,
      "available_stock": 8,
      "competitor_prices": [189.9, 194.9],
      "views_last_7d": 120,
      "sales_last_30d": 10,
      "conversion_rate": 0.05,
      "attributes": {"brand": "Sony", "condition": "new"}
    },
    "business_goal": "maximize_profit_and_engagement"
  }'
```
