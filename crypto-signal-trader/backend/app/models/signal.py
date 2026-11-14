"""Parsed trading signal model."""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import DECIMAL, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Signal(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "signals"

    source_message_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("telegram_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Instrument
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(64), default="binance", nullable=False)

    # Direction & type
    direction: Mapped[str] = mapped_column(String(8), nullable=False)   # BUY | SELL
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)  # MARKET | LIMIT

    # Prices (stored as string to preserve precision)
    entry_price: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)
    stop_loss: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)
    take_profit_1: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)
    take_profit_2: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)
    take_profit_3: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)

    # Risk
    risk_reward_ratio: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4), nullable=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)

    # State machine
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False, index=True
    )
    # PENDING → VALIDATED → EXECUTED | REJECTED | EXPIRED

    validation_errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    source_message: Mapped["TelegramMessage | None"] = relationship(  # noqa: F821
        "TelegramMessage", back_populates="signals"
    )
    positions: Mapped[list["Position"]] = relationship(  # noqa: F821
        "Position", back_populates="signal"
    )

    def __repr__(self) -> str:
        return f"<Signal {self.symbol} {self.direction} {self.status}>"
