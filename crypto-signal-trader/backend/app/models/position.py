"""Virtual paper-trading position model."""
from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Position(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "positions"

    signal_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("signals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)  # LONG | SHORT
    status: Mapped[str] = mapped_column(
        String(16), default="OPEN", nullable=False, index=True
    )  # OPEN | CLOSED | LIQUIDATED

    # Execution
    entry_price: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)
    exit_price: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)
    notional_value: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)

    # Risk levels
    stop_loss: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)
    take_profit_1: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)
    take_profit_2: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)
    take_profit_3: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)

    # P&L (updated by pnl_service)
    unrealized_pnl: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), default=Decimal("0"), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), default=Decimal("0"), nullable=False)
    fees_paid: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), default=Decimal("0"), nullable=False)

    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)  # TP1|TP2|TP3|SL|MANUAL

    # Relationships
    signal: Mapped["Signal | None"] = relationship("Signal", back_populates="positions")  # noqa: F821
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="positions")  # noqa: F821
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="position")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Position {self.symbol} {self.direction} {self.status}>"
