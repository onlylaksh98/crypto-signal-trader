"""
Portfolio Service
-----------------
Higher-level orchestration: process a validated signal end-to-end.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.signal import Signal
from app.services.market_data_service import MarketDataService
from app.services.paper_broker import PaperBroker
from app.services.risk_engine import RiskEngine
from app.services.signal_parser import ParsedSignal

logger = get_logger(__name__)


class PortfolioService:
    def __init__(
        self,
        db: AsyncSession,
        market_data: MarketDataService,
        risk_engine: RiskEngine,
    ) -> None:
        self._db = db
        self._market = market_data
        self._risk = risk_engine
        self._broker = PaperBroker(db)

    async def get_or_create_default(self) -> Portfolio:
        from app.core.config import settings

        result = await self._db.execute(
            select(Portfolio).where(Portfolio.is_default == True).limit(1)  # noqa: E712
        )
        portfolio = result.scalar_one_or_none()
        if portfolio is None:
            portfolio = Portfolio(
                name="Paper Portfolio",
                is_default=True,
                currency="USDT",
                initial_balance=Decimal(str(settings.paper_initial_balance_usdt)),
                cash_balance=Decimal(str(settings.paper_initial_balance_usdt)),
                total_equity=Decimal(str(settings.paper_initial_balance_usdt)),
                peak_equity=Decimal(str(settings.paper_initial_balance_usdt)),
            )
            self._db.add(portfolio)
            await self._db.flush()
            logger.info("portfolio_created", balance=portfolio.cash_balance)
        return portfolio

    async def execute_signal(self, signal: Signal, parsed: ParsedSignal) -> bool:
        """
        Full pipeline: get portfolio → get market price → size position → open.
        Returns True if execution succeeded.
        """
        portfolio = await self.get_or_create_default()

        # Get current market price
        price = await self._market.get_price(signal.symbol)
        if price is None:
            logger.error("no_market_price", symbol=signal.symbol)
            signal.status = "REJECTED"
            signal.validation_errors = "Could not fetch market price"
            return False

        # Count open positions
        result = await self._db.execute(
            select(Position).where(
                Position.portfolio_id == portfolio.id,
                Position.status == "OPEN",
            )
        )
        open_positions = result.scalars().all()

        # Size the position
        sizing = self._risk.calculate_position(
            signal=parsed,
            equity=portfolio.total_equity,
            cash=portfolio.cash_balance,
            current_price=price,
            open_position_count=len(open_positions),
        )

        if not sizing.approved:
            signal.status = "REJECTED"
            signal.validation_errors = sizing.rejection_reason
            logger.warning("signal_rejected_by_risk", reason=sizing.rejection_reason)
            return False

        try:
            position, order = await self._broker.open_position(
                portfolio=portfolio,
                signal=signal,
                sizing=sizing,
                market_price=price,
            )
            signal.status = "EXECUTED"
            logger.info("signal_executed", signal_id=str(signal.id))
            return True
        except Exception as exc:
            signal.status = "REJECTED"
            signal.validation_errors = str(exc)
            logger.error("execution_failed", error=str(exc))
            return False

    async def update_unrealized_pnl(self) -> None:
        """
        Refresh unrealized P&L for all open positions using current market prices.
        Called periodically by the background worker.
        """
        portfolio = await self.get_or_create_default()
        result = await self._db.execute(
            select(Position).where(
                Position.portfolio_id == portfolio.id,
                Position.status == "OPEN",
            )
        )
        positions = result.scalars().all()

        symbols = list({p.symbol for p in positions})
        if not symbols:
            portfolio.unrealized_pnl = Decimal("0")
            portfolio.total_equity = portfolio.cash_balance
            return

        prices = await self._market.get_prices_batch(symbols)
        total_unrealized = Decimal("0")

        for pos in positions:
            px = prices.get(pos.symbol)
            if px is None:
                continue
            if pos.direction == "LONG":
                pnl = (px - pos.entry_price) * pos.quantity
            else:
                pnl = (pos.entry_price - px) * pos.quantity
            pnl -= pos.fees_paid
            pos.unrealized_pnl = pnl
            total_unrealized += pnl

        portfolio.unrealized_pnl = total_unrealized
        portfolio.total_equity = portfolio.cash_balance + total_unrealized

        # Update peak equity & drawdown
        if portfolio.total_equity > portfolio.peak_equity:
            portfolio.peak_equity = portfolio.total_equity

        _, drawdown = self._risk.check_drawdown(portfolio.total_equity, portfolio.peak_equity)
        portfolio.max_drawdown = max(portfolio.max_drawdown, drawdown)

        await self._db.flush()
