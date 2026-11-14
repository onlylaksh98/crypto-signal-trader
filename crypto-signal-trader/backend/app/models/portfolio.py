"""Virtual portfolio (paper trading account)."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Portfolio(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "portfolios"

    name: Mapped[str] = mapped_column(String(128), default="Paper Portfolio", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USDT", nullable=False)

    # Balances
    initial_balance: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)
    cash_balance: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)
    total_equity: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)

    # P&L
    realized_pnl: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), default=Decimal("0"), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), default=Decimal("0"), nullable=False)
    daily_pnl: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), default=Decimal("0"), nullable=False)
    max_drawdown: Mapped[Decimal] = mapped_column(DECIMAL(8, 4), default=Decimal("0"), nullable=False)
    peak_equity: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)

    # Trade stats
    total_trades: Mapped[int] = mapped_column(default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(default=0, nullable=False)
    losing_trades: Mapped[int] = mapped_column(default=0, nullable=False)

    # Relationships
    positions: Mapped[list["Position"]] = relationship(  # noqa: F821
        "Position", back_populates="portfolio"
    )
    orders: Mapped[list["Order"]] = relationship(  # noqa: F821
        "Order", back_populates="portfolio"
    )
    equity_snapshots: Mapped[list["EquitySnapshot"]] = relationship(  # noqa: F821
        "EquitySnapshot", back_populates="portfolio"
    )

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades * 100

    def __repr__(self) -> str:
        return f"<Portfolio {self.name} equity={self.total_equity}>"
