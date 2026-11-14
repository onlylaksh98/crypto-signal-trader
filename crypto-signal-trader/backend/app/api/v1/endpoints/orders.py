"""Orders endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.order import Order
from app.schemas import OrderRead

router = APIRouter()


@router.get("", response_model=list[OrderRead])
async def list_orders(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).order_by(Order.created_at.desc()).limit(limit).offset(offset)
    )
    return [OrderRead.model_validate(o) for o in result.scalars().all()]
