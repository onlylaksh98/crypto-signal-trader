"""
Tests for the RiskEngine service.
Run with: pytest tests/test_risk_engine.py -v
"""
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.services.risk_engine import RiskEngine, PositionSizeResult
from app.services.signal_parser import ParsedSignal


@pytest.fixture
def engine() -> RiskEngine:
    return RiskEngine()


def _make_signal(**overrides) -> ParsedSignal:
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


# ── Basic sizing ──────────────────────────────────────────────────────────────


class TestBasicSizing:
    def test_position_approved(self, engine: RiskEngine):
        signal = _make_signal()
        result = engine.calculate_position(
            signal=signal,
            equity=Decimal("10000"),
            cash=Decimal("10000"),
            current_price=Decimal("42500"),
            open_position_count=0,
        )
        assert result.approved
        assert result.quantity > 0
        assert result.notional_value > 0
        assert result.fee_estimate > 0

    def test_position_size_proportional_to_equity(self, engine: RiskEngine):
        signal = _make_signal()
        result_small = engine.calculate_position(
            signal=signal,
            equity=Decimal("5000"),
            cash=Decimal("5000"),
            current_price=Decimal("42500"),
            open_position_count=0,
        )
        result_large = engine.calculate_position(
            signal=signal,
            equity=Decimal("50000"),
            cash=Decimal("50000"),
            current_price=Decimal("42500"),
            open_position_count=0,
        )
        assert result_large.notional_value > result_small.notional_value


# ── Rejection scenarios ───────────────────────────────────────────────────────


class TestRejection:
    @patch("app.services.risk_engine.settings")
    def test_max_positions_reached(self, mock_settings, engine: RiskEngine):
        mock_settings.paper_max_open_positions = 5
        signal = _make_signal()
        result = engine.calculate_position(
            signal=signal,
            equity=Decimal("10000"),
            cash=Decimal("10000"),
            current_price=Decimal("42500"),
            open_position_count=5,  # At max
        )
        assert not result.approved
        assert "max" in result.rejection_reason.lower()

    def test_zero_cash(self, engine: RiskEngine):
        signal = _make_signal()
        result = engine.calculate_position(
            signal=signal,
            equity=Decimal("10000"),
            cash=Decimal("0"),
            current_price=Decimal("42500"),
            open_position_count=0,
        )
        assert not result.approved


# ── Drawdown check ────────────────────────────────────────────────────────────


class TestDrawdown:
    def test_within_limit(self, engine: RiskEngine):
        within, pct = engine.check_drawdown(
            current_equity=Decimal("9500"),
            peak_equity=Decimal("10000"),
        )
        assert within
        assert pct == Decimal("5")

    def test_beyond_limit(self, engine: RiskEngine):
        within, pct = engine.check_drawdown(
            current_equity=Decimal("7500"),
            peak_equity=Decimal("10000"),
        )
        assert not within
        assert pct == Decimal("25")

    def test_zero_peak_equity(self, engine: RiskEngine):
        within, pct = engine.check_drawdown(
            current_equity=Decimal("0"),
            peak_equity=Decimal("0"),
        )
        assert within
        assert pct == Decimal("0")
