"""Raw Telegram message model."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class TelegramMessage(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "telegram_messages"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("telegram_channels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sender_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sender_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    processed: Mapped[bool] = mapped_column(default=False, nullable=False)
    signal_parsed: Mapped[bool] = mapped_column(default=False, nullable=False)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    channel: Mapped["TelegramChannel"] = relationship(  # noqa: F821
        "TelegramChannel", back_populates="messages"
    )
    signals: Mapped[list["Signal"]] = relationship(  # noqa: F821
        "Signal", back_populates="source_message"
    )

    def __repr__(self) -> str:
        return f"<TelegramMessage msg_id={self.message_id}>"
