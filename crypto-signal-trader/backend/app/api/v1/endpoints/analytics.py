"""Analytics endpoints — equity curve, performance metrics."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.equity_snapshot import EquitySnapshot
from app.models.portfolio import Portfolio
from app.schemas import EquitySnapshotRead

router = APIRouter()


@router.get("/equity-curve", response_model=list[EquitySnapshotRead])
async def get_equity_curve(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Returns equity curve snapshots for the last N days."""
    result = await db.execute(
        select(Portfolio).where(Portfolio.is_default == True).limit(1)  # noqa
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        return []

    since = datetime.now(timezone.utc) - timedelta(days=days)
    snap_result = await db.execute(
        select(EquitySnapshot)
        .where(
            EquitySnapshot.portfolio_id == portfolio.id,
            EquitySnapshot.timestamp >= since,
        )
        .order_by(EquitySnapshot.timestamp.asc())
        .limit(500)
    )
    return [EquitySnapshotRead.model_validate(s) for s in snap_result.scalars().all()]


@router.get("/performance")
async def get_performance(db: AsyncSession = Depends(get_db)):
    """Aggregated performance metrics for the analytics page."""
    result = await db.execute(
        select(Portfolio).where(Portfolio.is_default == True).limit(1)  # noqa
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        return {}

    return {
        "win_rate": portfolio.win_rate,
        "total_trades": portfolio.total_trades,
        "winning_trades": portfolio.winning_trades,
        "losing_trades": portfolio.losing_trades,
        "realized_pnl": float(portfolio.realized_pnl),
        "unrealized_pnl": float(portfolio.unrealized_pnl),
        "max_drawdown": float(portfolio.max_drawdown),
        "initial_balance": float(portfolio.initial_balance),
        "current_equity": float(portfolio.total_equity),
        "total_return_pct": float(
            (portfolio.total_equity - portfolio.initial_balance)
            / portfolio.initial_balance
            * 100
        ),
    }


@router.get("/market-hours")
async def get_market_hours():
    """Returns real-time stock market sessions, opening/closing times, dates, and active countdowns."""
    from app.services.market_hours_service import MarketHoursService
    return MarketHoursService.get_all_market_hours()

