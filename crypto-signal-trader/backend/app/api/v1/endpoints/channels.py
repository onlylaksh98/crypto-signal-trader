"""Telegram channel management endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.channel import TelegramChannel
from app.models.message import TelegramMessage
from app.schemas import ChannelCreate, ChannelRead, ChannelUpdate, MessageRead

router = APIRouter()


@router.get("", response_model=list[ChannelRead])
async def list_channels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TelegramChannel).order_by(TelegramChannel.created_at.desc()))
    return [ChannelRead.model_validate(c) for c in result.scalars().all()]


@router.post("", response_model=ChannelRead, status_code=status.HTTP_201_CREATED)
async def add_channel(payload: ChannelCreate, db: AsyncSession = Depends(get_db)):
    """Add a new channel to monitor. Resolves via Telegram if client connected."""
    identifier = payload.channel_identifier.strip()
    channel_id = identifier.lstrip("@")

    # Check duplicate
    result = await db.execute(
        select(TelegramChannel).where(TelegramChannel.channel_id == channel_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Channel '{identifier}' is already configured",
        )

    # Try to resolve via Telegram service (app state)
    from app.main import app_state  # type: ignore
    tg = getattr(app_state, "telegram_service", None)
    channel_title = None
    channel_username = None

    if tg and tg.is_connected:
        try:
            meta = await tg.add_channel(identifier)
            channel_id = meta["channel_id"]
            channel_title = meta.get("channel_title")
            channel_username = meta.get("channel_username")
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Telegram lookup failed: {exc}",
            )

    channel = TelegramChannel(
        channel_id=channel_id,
        channel_username=channel_username or identifier.lstrip("@"),
        channel_title=channel_title,
        is_active=True,
        is_monitored=True,
    )
    db.add(channel)
    await db.flush()
    await db.refresh(channel)
    return ChannelRead.model_validate(channel)


@router.patch("/{channel_id}", response_model=ChannelRead)
async def update_channel(
    channel_id: uuid.UUID,
    payload: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TelegramChannel).where(TelegramChannel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if payload.is_active is not None:
        channel.is_active = payload.is_active
    if payload.is_monitored is not None:
        channel.is_monitored = payload.is_monitored
    await db.flush()
    await db.refresh(channel)
    return ChannelRead.model_validate(channel)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(channel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TelegramChannel).where(TelegramChannel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    await db.delete(channel)


@router.get("/{channel_id}/messages", response_model=list[MessageRead])
async def get_channel_messages(
    channel_id: uuid.UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TelegramMessage)
        .where(TelegramMessage.channel_id == channel_id)
        .order_by(TelegramMessage.created_at.desc())
        .limit(limit)
    )
    return [MessageRead.model_validate(m) for m in result.scalars().all()]
