"""
FastAPI dependency helpers — provide access to application-level services
stored on the global AppState singleton.
"""
from __future__ import annotations

from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


def get_telegram_service():
    """
    FastAPI dependency that returns the running TelegramService instance,
    or None if Telegram was not configured / connected.
    """
    from app.main import app_state  # type: ignore[attr-defined]

    svc = getattr(app_state, "telegram_service", None)
    return svc


def get_market_data_service():
    """
    FastAPI dependency that returns the running MarketDataService instance,
    or None if it failed to connect.
    """
    from app.main import app_state  # type: ignore[attr-defined]

    svc = getattr(app_state, "market_data_service", None)
    return svc
