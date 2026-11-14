"""Simulated order model (paper trading only)."""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import DECIMAL, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Order(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    position_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("positions.id", ondelete="SET NULL"),
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
    side: Mapped[str] = mapped_column(String(8), nullable=False)   # BUY | SELL
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)  # MARKET | LIMIT | STOP
    status: Mapped[str] = mapped_column(
        String(16), default="PENDING", nullable=False, index=True
    )  # PENDING | FILLED | CANCELLED | REJECTED

    # PAPER TRADING ONLY — explicitly marked
    execution_mode: Mapped[str] = mapped_column(
        String(32), default="PAPER", nullable=False
    )

    requested_quantity: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)
    filled_quantity: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), default=Decimal("0"), nullable=False)
    requested_price: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)
    filled_price: Mapped[Decimal | None] = mapped_column(DECIMAL(24, 8), nullable=True)
    slippage_bps: Mapped[int] = mapped_column(default=0, nullable=False)
    fee: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), default=Decimal("0"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    position: Mapped["Position | None"] = relationship("Position", back_populates="orders")  # noqa: F821
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="orders")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Order [{self.execution_mode}] {self.symbol} {self.side} {self.status}>"
