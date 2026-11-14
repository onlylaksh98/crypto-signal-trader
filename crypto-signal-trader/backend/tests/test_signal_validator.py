"""
Tests for the SignalValidator service.
Run with: pytest tests/test_signal_validator.py -v
"""
from decimal import Decimal

import pytest

from app.services.signal_parser import ParsedSignal
from app.services.signal_validator import SignalValidator


@pytest.fixture
def validator() -> SignalValidator:
    return SignalValidator()


def _make_signal(**overrides) -> ParsedSignal:
    """Helper to create a ParsedSignal with sensible defaults."""
    defaults = dict(
        symbol="BTCUSDT",
        direction="BUY",
        order_type="MARKET",
        entry_price=Decimal("42500"),
        stop_loss=Decimal("41000"),
        take_profits=[Decimal("44000")],
        confidence_score=Decimal("80"),
    )
    defaults.update(overrides)
    return ParsedSignal(**defaults)


# ── Valid signals ─────────────────────────────────────────────────────────────


class TestValidSignals:
    def test_fully_formed_signal(self, validator: SignalValidator):
        signal = _make_signal()
        result = validator.validate(signal)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_sell_signal_valid(self, validator: SignalValidator):
        signal = _make_signal(
            direction="SELL",
            entry_price=Decimal("42500"),
            stop_loss=Decimal("44000"),  # Above entry for SELL
            take_profits=[Decimal("40000")],  # Below entry for SELL
        )
        result = validator.validate(signal)
        assert result.is_valid


# ── Invalid signals ───────────────────────────────────────────────────────────


class TestInvalidSignals:
    def test_missing_symbol(self, validator: SignalValidator):
        signal = _make_signal(symbol="")
        result = validator.validate(signal)
        assert not result.is_valid
        assert any("symbol" in e.lower() for e in result.errors)

    def test_missing_direction(self, validator: SignalValidator):
        signal = _make_signal(direction="")
        result = validator.validate(signal)
        assert not result.is_valid
        assert any("direction" in e.lower() for e in result.errors)

    def test_low_confidence(self, validator: SignalValidator):
        signal = _make_signal(confidence_score=Decimal("10"))
        result = validator.validate(signal)
        assert not result.is_valid
        assert any("confidence" in e.lower() for e in result.errors)

    def test_buy_sl_above_entry(self, validator: SignalValidator):
        signal = _make_signal(
            direction="BUY",
            entry_price=Decimal("42500"),
            stop_loss=Decimal("43000"),  # SL above entry = invalid for BUY
        )
        result = validator.validate(signal)
        assert not result.is_valid

    def test_sell_sl_below_entry(self, validator: SignalValidator):
        signal = _make_signal(
            direction="SELL",
            entry_price=Decimal("42500"),
            stop_loss=Decimal("42000"),  # SL below entry = invalid for SELL
        )
        result = validator.validate(signal)
        assert not result.is_valid

    def test_buy_tp_below_entry(self, validator: SignalValidator):
        signal = _make_signal(
            direction="BUY",
            entry_price=Decimal("42500"),
            take_profits=[Decimal("40000")],  # TP below entry = invalid for BUY
        )
        result = validator.validate(signal)
        assert not result.is_valid


# ── Warnings ──────────────────────────────────────────────────────────────────


class TestWarnings:
    def test_warning_no_stop_loss(self, validator: SignalValidator):
        signal = _make_signal(stop_loss=None)
        result = validator.validate(signal)
        assert result.is_valid  # still valid, just a warning
        assert any("stop loss" in w.lower() for w in result.warnings)

    def test_warning_no_take_profit(self, validator: SignalValidator):
        signal = _make_signal(take_profits=[])
        result = validator.validate(signal)
        assert result.is_valid
        assert any("take profit" in w.lower() for w in result.warnings)

    def test_warning_bad_risk_reward(self, validator: SignalValidator):
        signal = _make_signal(
            entry_price=Decimal("42500"),
            stop_loss=Decimal("41000"),
            take_profits=[Decimal("42800")],  # R:R < 1
        )
        result = validator.validate(signal)
        assert any("risk/reward" in w.lower() for w in result.warnings)

    def test_warning_price_deviation(self, validator: SignalValidator):
        signal = _make_signal(
            order_type="LIMIT",
            entry_price=Decimal("42500"),
        )
        # Current price far from entry
        result = validator.validate(signal, current_price=Decimal("50000"))
        assert any("deviates" in w.lower() for w in result.warnings)
