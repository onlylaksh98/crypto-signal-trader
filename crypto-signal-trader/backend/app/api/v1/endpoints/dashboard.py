"""Dashboard endpoint — overview stats for the main page."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.equity_snapshot import EquitySnapshot
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.signal import Signal
from app.schemas import DashboardStats, EquitySnapshotRead, OrderRead, PortfolioRead, SignalRead

router = APIRouter()


@router.get("", response_model=DashboardStats)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Return all data needed for the overview dashboard."""
    from app.main import app_state  # type: ignore[attr-defined]
    from app.services.portfolio_service import PortfolioService
    from app.services.market_data_service import MarketDataService
    from app.services.risk_engine import RiskEngine

    # Portfolio
    result = await db.execute(select(Portfolio).where(Portfolio.is_default == True).limit(1))  # noqa
    portfolio = result.scalar_one_or_none()

    if portfolio is None:
        # Auto-create default portfolio
        ps = PortfolioService(db, MarketDataService(), RiskEngine())
        portfolio = await ps.get_or_create_default()
        await db.commit()

    # Open positions count
    pos_result = await db.execute(
        select(func.count(Position.id)).where(
            Position.portfolio_id == portfolio.id,
            Position.status == "OPEN",
        )
    )
    open_count = pos_result.scalar_one() or 0

    # Recent signals (last 10)
    sig_result = await db.execute(
        select(Signal).order_by(Signal.created_at.desc()).limit(10)
    )
    recent_signals = sig_result.scalars().all()

    # Recent orders (last 10)
    ord_result = await db.execute(
        select(Order).order_by(Order.created_at.desc()).limit(10)
    )
    recent_orders = ord_result.scalars().all()

    # Equity curve (last 100 snapshots)
    eq_result = await db.execute(
        select(EquitySnapshot)
        .where(EquitySnapshot.portfolio_id == portfolio.id)
        .order_by(EquitySnapshot.timestamp.asc())
        .limit(100)
    )
    equity_curve = eq_result.scalars().all()

    # Real connection status from app_state
    tg = getattr(app_state, "telegram_service", None)
    md = getattr(app_state, "market_data_service", None)

    return DashboardStats(
        portfolio=PortfolioRead.model_validate(portfolio),
        open_positions_count=open_count,
        recent_signals=[SignalRead.model_validate(s) for s in recent_signals],
        recent_orders=[OrderRead.model_validate(o) for o in recent_orders],
        equity_curve=[EquitySnapshotRead.model_validate(e) for e in equity_curve],
        telegram_connected=bool(tg and tg.is_connected),
        market_data_connected=bool(md and md.is_connected),
        is_paper_trading=True,
    )

