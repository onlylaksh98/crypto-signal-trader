"""
Signal Validator Service
------------------------
Validates a ParsedSignal against business rules and current market price.
Independent of the database — takes pure data objects.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from app.services.signal_parser import ParsedSignal
from app.core.logging import get_logger

logger = get_logger(__name__)

MIN_CONFIDENCE = Decimal("30")
MAX_PRICE_DEVIATION_PCT = Decimal("5")  # entry must be within 5% of market price


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SignalValidator:
    """
    Validates a parsed signal.
    Raises no exceptions — returns a ValidationResult.
    """

    def validate(
        self,
        signal: ParsedSignal,
        current_price: Optional[Decimal] = None,
    ) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        # ── Required fields ───────────────────────────────────────────────────
        if not signal.symbol:
            errors.append("Missing symbol")
        if not signal.direction:
            errors.append("Missing direction (BUY/SELL)")

        # ── Confidence threshold ──────────────────────────────────────────────
        if signal.confidence_score < MIN_CONFIDENCE:
            errors.append(
                f"Confidence score {signal.confidence_score} is below minimum {MIN_CONFIDENCE}"
            )

        # ── Price sanity checks ───────────────────────────────────────────────
        if signal.entry_price and signal.entry_price <= 0:
            errors.append("Entry price must be positive")

        if signal.stop_loss and signal.entry_price:
            if signal.direction == "BUY" and signal.stop_loss >= signal.entry_price:
                errors.append("Stop loss must be below entry price for BUY signals")
            elif signal.direction == "SELL" and signal.stop_loss <= signal.entry_price:
                errors.append("Stop loss must be above entry price for SELL signals")

        if signal.take_profits and signal.entry_price:
            tp1 = signal.take_profits[0]
            if signal.direction == "BUY" and tp1 <= signal.entry_price:
                errors.append("Take profit must be above entry price for BUY signals")
            elif signal.direction == "SELL" and tp1 >= signal.entry_price:
                errors.append("Take profit must be below entry price for SELL signals")

        # ── Risk/reward ───────────────────────────────────────────────────────
        rrr = signal.risk_reward_ratio
        if rrr is not None and rrr < Decimal("1"):
            warnings.append(f"Risk/reward ratio {rrr:.2f} is below 1:1")

        # ── Market price proximity ────────────────────────────────────────────
        if current_price and signal.entry_price and signal.order_type == "LIMIT":
            deviation = abs(signal.entry_price - current_price) / current_price * 100
            if deviation > MAX_PRICE_DEVIATION_PCT:
                warnings.append(
                    f"Entry price {signal.entry_price} deviates {deviation:.1f}% from "
                    f"current market price {current_price}"
                )

        if not signal.stop_loss:
            warnings.append("No stop loss defined — risk is uncontrolled")

        if not signal.take_profits:
            warnings.append("No take profit levels defined")

        is_valid = len(errors) == 0
        logger.info(
            "signal_validated",
            symbol=signal.symbol,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        )
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
