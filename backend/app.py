from fastapi import FastAPI

from routes.agent import router as agent_router
from routes.auth import router as auth_router
from routes.health import router as health_router
from routes.operations import router as operations_router
from routes.pricing import router as pricing_router
from routes.questions import router as questions_router
from routes.webhooks import router as webhooks_router


app = FastAPI(
    title="Mercado Livre AI Selling Agent",
    version="0.1.0",
    description="Backend API for listing optimization, pricing, and buyer engagement.",
)

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(agent_router)
app.include_router(operations_router)
app.include_router(pricing_router)
app.include_router(questions_router)
app.include_router(webhooks_router)
