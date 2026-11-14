"""Signals endpoints — list, detail, manual create."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.signal import Signal
from app.schemas import SignalCreate, SignalRead

router = APIRouter()


@router.get("", response_model=list[SignalRead])
async def list_signals(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Signal).order_by(Signal.created_at.desc()).limit(limit).offset(offset)
    if status:
        q = q.where(Signal.status == status.upper())
    result = await db.execute(q)
    return [SignalRead.model_validate(s) for s in result.scalars().all()]


@router.get("/{signal_id}", response_model=SignalRead)
async def get_signal(signal_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return SignalRead.model_validate(signal)


@router.post("", response_model=SignalRead, status_code=201)
async def create_signal(payload: SignalCreate, db: AsyncSession = Depends(get_db)):
    """Manually create and immediately execute a paper-trade signal."""
    from app.services.signal_parser import ParsedSignal
    from app.services.signal_validator import SignalValidator
    from app.services.market_data_service import MarketDataService
    from app.services.risk_engine import RiskEngine
    from app.services.portfolio_service import PortfolioService

    signal = Signal(
        symbol=payload.symbol.upper(),
        direction=payload.direction.upper(),
        order_type=payload.order_type.upper(),
        entry_price=payload.entry_price,
        stop_loss=payload.stop_loss,
        take_profit_1=payload.take_profit_1,
        take_profit_2=payload.take_profit_2,
        take_profit_3=payload.take_profit_3,
        status="PENDING",
        notes=payload.notes,
    )
    db.add(signal)
    await db.flush()

    parsed = ParsedSignal(
        symbol=signal.symbol,
        direction=signal.direction,
        order_type=signal.order_type,
        entry_price=signal.entry_price,
        stop_loss=signal.stop_loss,
        take_profits=[tp for tp in [signal.take_profit_1, signal.take_profit_2, signal.take_profit_3] if tp],
        confidence_score=__import__("decimal").Decimal("80"),
    )

    market = MarketDataService()
    await market.connect()
    ps = PortfolioService(db, market, RiskEngine())
    await ps.execute_signal(signal, parsed)
    await market.close()

    await db.refresh(signal)

    # Index in RAG vector store
    try:
        from app.services.rag.rag_service import rag_service
        await rag_service.initialize()
        await rag_service.index_signal(
            signal_id=str(signal.id),
            symbol=signal.symbol,
            direction=signal.direction,
            order_type=signal.order_type,
            entry_price=float(signal.entry_price) if signal.entry_price else None,
            stop_loss=float(signal.stop_loss) if signal.stop_loss else None,
            take_profit_1=float(signal.take_profit_1) if signal.take_profit_1 else None,
            take_profit_2=float(signal.take_profit_2) if signal.take_profit_2 else None,
            confidence_score=float(signal.confidence_score) if signal.confidence_score else None,
            risk_reward_ratio=float(signal.risk_reward_ratio) if signal.risk_reward_ratio else None,
            notes=signal.notes,
            status=signal.status,
            channel_name="Manual Entry / Terminal",
        )
    except Exception as r_err:
        pass

    return SignalRead.model_validate(signal)
