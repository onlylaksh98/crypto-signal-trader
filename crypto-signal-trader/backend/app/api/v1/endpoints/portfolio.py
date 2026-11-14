"""Portfolio endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.portfolio import Portfolio
from app.schemas import PortfolioRead

router = APIRouter()


@router.get("", response_model=PortfolioRead)
async def get_portfolio(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Portfolio).where(Portfolio.is_default == True).limit(1))  # noqa
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        from app.services.portfolio_service import PortfolioService
        from app.services.market_data_service import MarketDataService
        from app.services.risk_engine import RiskEngine
        ps = PortfolioService(db, MarketDataService(), RiskEngine())
        portfolio = await ps.get_or_create_default()
    return PortfolioRead.model_validate(portfolio)
