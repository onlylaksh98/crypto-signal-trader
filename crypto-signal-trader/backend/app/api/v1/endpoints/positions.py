"""Positions endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.schemas import PositionRead

router = APIRouter()


@router.get("", response_model=list[PositionRead])
async def list_positions(
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(Position).order_by(Position.created_at.desc()).limit(limit)
    if status:
        q = q.where(Position.status == status.upper())
    result = await db.execute(q)
    return [PositionRead.model_validate(p) for p in result.scalars().all()]


@router.get("/{position_id}", response_model=PositionRead)
async def get_position(position_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).where(Position.id == position_id))
    pos = result.scalar_one_or_none()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")
    return PositionRead.model_validate(pos)


@router.post("/{position_id}/close", response_model=PositionRead)
async def close_position(position_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Manually close an open paper position at current market price."""
    from app.services.market_data_service import MarketDataService
    from app.services.paper_broker import PaperBroker

    result = await db.execute(select(Position).where(Position.id == position_id))
    pos = result.scalar_one_or_none()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")
    if pos.status != "OPEN":
        raise HTTPException(status_code=400, detail=f"Position is {pos.status}, not OPEN")

    port_result = await db.execute(
        select(Portfolio).where(Portfolio.id == pos.portfolio_id)
    )
    portfolio = port_result.scalar_one()

    market = MarketDataService()
    await market.connect()
    price = await market.get_price(pos.symbol)
    await market.close()

    if price is None:
        raise HTTPException(status_code=503, detail="Could not fetch market price")

    broker = PaperBroker(db)
    pos, _ = await broker.close_position(portfolio, pos, price, reason="MANUAL")
    await db.flush()
    return PositionRead.model_validate(pos)
