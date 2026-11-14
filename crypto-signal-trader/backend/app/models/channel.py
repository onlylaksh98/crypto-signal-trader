"""Telegram channel configuration model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class TelegramChannel(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "telegram_channels"

    channel_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    channel_username: Mapped[str | None] = mapped_column(String(256), nullable=True)
    channel_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_monitored: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Stats
    messages_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    messages_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    messages_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    signals_parsed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    messages: Mapped[list["TelegramMessage"]] = relationship(  # noqa: F821
        "TelegramMessage", back_populates="channel", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<TelegramChannel {self.channel_username or self.channel_id}>"
