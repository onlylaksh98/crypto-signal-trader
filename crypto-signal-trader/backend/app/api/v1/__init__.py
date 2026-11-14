"""API v1 router — aggregates all endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    dashboard,
    channels,
    signals,
    positions,
    orders,
    portfolio,
    analytics,
    rag,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(channels.router, prefix="/channels", tags=["Telegram Channels"])
api_router.include_router(signals.router, prefix="/signals", tags=["Signals"])
api_router.include_router(positions.router, prefix="/positions", tags=["Positions"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG & AI Copilot"])
