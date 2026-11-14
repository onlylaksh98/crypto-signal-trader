"""Equity curve snapshots for chart data."""
from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin


class EquitySnapshot(UUIDPKMixin, Base):
    __tablename__ = "equity_snapshots"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    equity: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)
    cash: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)

    portfolio: Mapped["Portfolio"] = relationship(  # noqa: F821
        "Portfolio", back_populates="equity_snapshots"
    )
