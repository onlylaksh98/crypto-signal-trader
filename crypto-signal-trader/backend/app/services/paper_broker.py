"""
Paper Broker Service
--------------------
Simulates order execution deterministically. PAPER TRADING ONLY.
Never submits real orders to any exchange.

All executions are internal bookkeeping with slippage simulation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.signal import Signal
from app.services.risk_engine import PositionSizeResult

logger = get_logger(__name__)

TAKER_FEE = Decimal("0.001")


class PaperBroker:
    """
    Executes simulated trades against a virtual Portfolio.
    Strictly enforces PAPER mode — no live exchange calls.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def open_position(
        self,
        portfolio: Portfolio,
        signal: Signal,
        sizing: PositionSizeResult,
        market_price: Decimal,
    ) -> tuple[Position, Order]:
        """
        Opens a paper position and records the simulated fill order.
        Returns (Position, Order).
        """
        assert settings.paper_trading_enabled, "PAPER TRADING MUST BE ENABLED"

        slippage = Decimal(str(settings.paper_slippage_bps)) / Decimal("10000")
        if signal.direction == "BUY":
            fill_price = market_price * (1 + slippage)
        else:
            fill_price = market_price * (1 - slippage)

        fee = sizing.notional_value * TAKER_FEE
        total_cost = sizing.notional_value + fee

        if total_cost > portfolio.cash_balance:
            raise ValueError(
                f"Insufficient paper cash: need {total_cost}, have {portfolio.cash_balance}"
            )

        now = datetime.now(timezone.utc)

        # Create position
        position = Position(
            portfolio_id=portfolio.id,
            signal_id=signal.id,
            symbol=signal.symbol,
            direction="LONG" if signal.direction == "BUY" else "SHORT",
            status="OPEN",
            entry_price=fill_price,
            quantity=sizing.quantity,
            notional_value=sizing.notional_value,
            stop_loss=signal.stop_loss,
            take_profit_1=signal.take_profit_1,
            take_profit_2=signal.take_profit_2,
            take_profit_3=signal.take_profit_3,
            fees_paid=fee,
            opened_at=now,
        )
        self._db.add(position)

        # Record the simulated order — PAPER mode is hardcoded
        order = Order(
            portfolio_id=portfolio.id,
            symbol=signal.symbol,
            side=signal.direction,
            order_type=signal.order_type,
            status="FILLED",
            execution_mode="PAPER",          # ← always PAPER
            requested_quantity=sizing.quantity,
            filled_quantity=sizing.quantity,
            requested_price=signal.entry_price,
            filled_price=fill_price,
            slippage_bps=settings.paper_slippage_bps,
            fee=fee,
            notes=f"Paper fill at {fill_price} (slippage {settings.paper_slippage_bps}bps)",
        )
        self._db.add(order)

        # Deduct from cash
        portfolio.cash_balance -= total_cost
        portfolio.total_equity = portfolio.cash_balance + portfolio.unrealized_pnl

        await self._db.flush()

        # Attach order to position
        order.position_id = position.id

        logger.info(
            "paper_position_opened",
            symbol=signal.symbol,
            fill_price=str(fill_price),
            quantity=str(sizing.quantity),
            fee=str(fee),
        )
        return position, order

    async def close_position(
        self,
        portfolio: Portfolio,
        position: Position,
        market_price: Decimal,
        reason: str = "MANUAL",
    ) -> tuple[Position, Order]:
        """Closes an open paper position."""
        assert settings.paper_trading_enabled, "PAPER TRADING MUST BE ENABLED"
        assert position.status == "OPEN", f"Position {position.id} is not open"

        slippage = Decimal(str(settings.paper_slippage_bps)) / Decimal("10000")
        # Closing a LONG means selling → price goes down with slippage
        if position.direction == "LONG":
            fill_price = market_price * (1 - slippage)
        else:
            fill_price = market_price * (1 + slippage)

        fee = position.notional_value * TAKER_FEE
        gross_pnl = (fill_price - position.entry_price) * position.quantity
        if position.direction == "SHORT":
            gross_pnl = -gross_pnl
        net_pnl = gross_pnl - fee - position.fees_paid

        proceeds = position.notional_value + gross_pnl - fee

        now = datetime.now(timezone.utc)
        position.status = "CLOSED"
        position.exit_price = fill_price
        position.realized_pnl = net_pnl
        position.unrealized_pnl = Decimal("0")
        position.fees_paid += fee
        position.closed_at = now
        position.close_reason = reason

        order = Order(
            portfolio_id=portfolio.id,
            position_id=position.id,
            symbol=position.symbol,
            side="SELL" if position.direction == "LONG" else "BUY",
            order_type="MARKET",
            status="FILLED",
            execution_mode="PAPER",
            requested_quantity=position.quantity,
            filled_quantity=position.quantity,
            filled_price=fill_price,
            slippage_bps=settings.paper_slippage_bps,
            fee=fee,
            notes=f"Close reason: {reason}",
        )
        self._db.add(order)

        # Return cash
        portfolio.cash_balance += proceeds
        portfolio.realized_pnl += net_pnl

        # Update win/loss stats
        portfolio.total_trades += 1
        if net_pnl > 0:
            portfolio.winning_trades += 1
        else:
            portfolio.losing_trades += 1

        # Update peak equity
        if portfolio.cash_balance > portfolio.peak_equity:
            portfolio.peak_equity = portfolio.cash_balance

        await self._db.flush()

        logger.info(
            "paper_position_closed",
            symbol=position.symbol,
            fill_price=str(fill_price),
            net_pnl=str(net_pnl),
            reason=reason,
        )
        return position, order
