"""
Risk Engine Service
-------------------
Calculates position sizes and checks portfolio-level risk limits.
All calculations are in paper-trading context only.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.signal_parser import ParsedSignal

logger = get_logger(__name__)

MAKER_FEE = Decimal("0.001")   # 0.1% maker fee simulation
TAKER_FEE = Decimal("0.001")   # 0.1% taker fee simulation


@dataclass
class PositionSizeResult:
    quantity: Decimal
    notional_value: Decimal
    risk_amount: Decimal
    position_pct: Decimal
    fee_estimate: Decimal
    approved: bool
    rejection_reason: Optional[str] = None


class RiskEngine:
    """
    Deterministic, stateless risk calculator.
    Takes portfolio state and signal; returns position sizing and approval.
    """

    def calculate_position(
        self,
        signal: ParsedSignal,
        equity: Decimal,
        cash: Decimal,
        current_price: Decimal,
        open_position_count: int,
    ) -> PositionSizeResult:
        # ── Max positions check ───────────────────────────────────────────────
        if open_position_count >= settings.paper_max_open_positions:
            return PositionSizeResult(
                quantity=Decimal("0"),
                notional_value=Decimal("0"),
                risk_amount=Decimal("0"),
                position_pct=Decimal("0"),
                fee_estimate=Decimal("0"),
                approved=False,
                rejection_reason=f"Max open positions ({settings.paper_max_open_positions}) reached",
            )

        # ── Compute notional value ────────────────────────────────────────────
        size_pct = Decimal(str(settings.paper_default_position_size_pct)) / 100
        max_size_pct = Decimal(str(settings.risk_max_position_size_pct)) / 100

        notional = (equity * size_pct).quantize(Decimal("0.01"))
        notional = min(notional, equity * max_size_pct)
        notional = min(notional, cash)  # can't spend more than available cash

        if notional <= 0:
            return PositionSizeResult(
                quantity=Decimal("0"),
                notional_value=Decimal("0"),
                risk_amount=Decimal("0"),
                position_pct=Decimal("0"),
                fee_estimate=Decimal("0"),
                approved=False,
                rejection_reason="Insufficient cash balance",
            )

        # ── Slippage-adjusted execution price ─────────────────────────────────
        slippage = Decimal(str(settings.paper_slippage_bps)) / Decimal("10000")
        if signal.direction == "BUY":
            exec_price = current_price * (1 + slippage)
        else:
            exec_price = current_price * (1 - slippage)

        quantity = (notional / exec_price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
        fee = notional * TAKER_FEE

        # ── Risk amount (distance to stop loss) ───────────────────────────────
        if signal.stop_loss and exec_price:
            risk_per_unit = abs(exec_price - signal.stop_loss)
            risk_amount = risk_per_unit * quantity
        else:
            risk_amount = notional * Decimal("0.02")  # assume 2% risk if no SL

        position_pct = (notional / equity * 100).quantize(Decimal("0.01"))

        logger.info(
            "position_sized",
            symbol=signal.symbol,
            notional=str(notional),
            quantity=str(quantity),
            exec_price=str(exec_price),
            risk_amount=str(risk_amount),
        )

        return PositionSizeResult(
            quantity=quantity,
            notional_value=notional,
            risk_amount=risk_amount,
            position_pct=position_pct,
            fee_estimate=fee,
            approved=True,
        )

    def check_drawdown(self, current_equity: Decimal, peak_equity: Decimal) -> tuple[bool, Decimal]:
        """Returns (within_limit, drawdown_pct)."""
        if peak_equity <= 0:
            return True, Decimal("0")
        drawdown_pct = (peak_equity - current_equity) / peak_equity * 100
        limit = Decimal(str(settings.risk_max_drawdown_pct))
        return drawdown_pct < limit, drawdown_pct
