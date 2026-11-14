"""
Tests for the SignalParser service.
Run with: pytest tests/test_signal_parser.py -v
"""
from decimal import Decimal

import pytest

from app.services.signal_parser import SignalParser, ParsedSignal


@pytest.fixture
def parser() -> SignalParser:
    return SignalParser()


# ── Basic buy signal ──────────────────────────────────────────────────────────


class TestBasicBuySignal:
    def test_buy_btcusdt(self, parser: SignalParser):
        text = """
        🚀 BTCUSDT BUY
        Entry: 42500
        Stop Loss: 41000
        TP1: 44000
        TP2: 46000
        """
        result = parser.parse(text)

        assert result.is_valid
        assert result.symbol == "BTCUSDT"
        assert result.direction == "BUY"
        assert result.entry_price == Decimal("42500")
        assert result.stop_loss == Decimal("41000")
        assert len(result.take_profits) >= 1
        assert result.take_profits[0] == Decimal("44000")
        assert result.confidence_score >= Decimal("30")

    def test_long_keyword(self, parser: SignalParser):
        result = parser.parse("LONG ETHUSDT Entry: 3200 SL: 3100 TP1: 3400")
        assert result.direction == "BUY"
        assert result.symbol == "ETHUSDT"

    def test_bullish_keyword(self, parser: SignalParser):
        result = parser.parse("SOLUSDT Bullish Entry 150 SL 140 TP 1: 170")
        assert result.direction == "BUY"


# ── Basic sell signal ─────────────────────────────────────────────────────────


class TestBasicSellSignal:
    def test_sell_ethusdt(self, parser: SignalParser):
        text = "SELL ETHUSDT Entry: 3500 Stop Loss: 3700 Target 1: 3200"
        result = parser.parse(text)

        assert result.is_valid
        assert result.symbol == "ETHUSDT"
        assert result.direction == "SELL"
        assert result.entry_price == Decimal("3500")

    def test_short_keyword(self, parser: SignalParser):
        result = parser.parse("Short BTCUSDT sell at 42000 SL 43000")
        assert result.direction == "SELL"


# ── Symbol extraction ─────────────────────────────────────────────────────────


class TestSymbolExtraction:
    def test_symbol_with_usdt_suffix(self, parser: SignalParser):
        result = parser.parse("Buy ADAUSDT at 0.45")
        assert result.symbol == "ADAUSDT"

    def test_bare_symbol_appends_usdt(self, parser: SignalParser):
        result = parser.parse("BUY SOL Entry: 150")
        assert result.symbol == "SOLUSDT"

    def test_unknown_symbol_no_match(self, parser: SignalParser):
        result = parser.parse("Buy some random thing at 100")
        assert result.symbol == ""
        assert not result.is_valid


# ── Confidence scoring ────────────────────────────────────────────────────────


class TestConfidenceScoring:
    def test_high_confidence_full_signal(self, parser: SignalParser):
        text = "BUY BTCUSDT Entry: 42500 SL: 41000 TP1: 44000 TP2: 46000 TP3: 48000"
        result = parser.parse(text)
        # symbol(20) + direction(20) + entry(15) + SL(15) + 3 TPs(30) = 100
        assert result.confidence_score >= Decimal("80")

    def test_low_confidence_minimal_signal(self, parser: SignalParser):
        text = "BUY BTC"
        result = parser.parse(text)
        # Only symbol + direction
        assert result.confidence_score <= Decimal("50")


# ── Risk/reward ratio ────────────────────────────────────────────────────────


class TestRiskReward:
    def test_risk_reward_calculated(self, parser: SignalParser):
        text = "BUY ETHUSDT Entry: 3000 SL: 2900 TP1: 3200"
        result = parser.parse(text)
        # Risk: 3000 - 2900 = 100, Reward: 3200 - 3000 = 200 → RRR = 2.0
        assert result.risk_reward_ratio is not None
        assert result.risk_reward_ratio == Decimal("2")

    def test_no_risk_reward_without_sl(self, parser: SignalParser):
        text = "BUY ETHUSDT Entry: 3000 TP1: 3200"
        result = parser.parse(text)
        assert result.risk_reward_ratio is None


# ── Edge cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_text(self, parser: SignalParser):
        result = parser.parse("")
        assert not result.is_valid

    def test_non_trading_text(self, parser: SignalParser):
        result = parser.parse("Good morning everyone! Have a great day 🌅")
        assert not result.is_valid

    def test_ambiguous_direction(self, parser: SignalParser):
        # Both BUY and SELL appear — should pick first
        text = "Buy BTCUSDT but if it breaks down sell at 40000"
        result = parser.parse(text)
        assert result.direction == "BUY"
        assert "ambiguous" in result.notes[0].lower()

    def test_commas_in_numbers(self, parser: SignalParser):
        text = "BUY BTCUSDT Entry: 42,500 SL: 41,000 TP1: 44,000"
        result = parser.parse(text)
        assert result.entry_price == Decimal("42500")

    def test_multiple_take_profits(self, parser: SignalParser):
        text = "BUY BTCUSDT Entry: 42500 SL: 41000 TP1: 44000 TP2: 46000 TP3: 48000"
        result = parser.parse(text)
        assert len(result.take_profits) == 3
        assert result.take_profit_1 == Decimal("44000")
        assert result.take_profit_2 == Decimal("46000")
        assert result.take_profit_3 == Decimal("48000")

    def test_order_type_market(self, parser: SignalParser):
        result = parser.parse("BUY BTCUSDT market order at 42500")
        assert result.order_type == "MARKET"

    def test_order_type_limit(self, parser: SignalParser):
        result = parser.parse("LIMIT order BUY BTCUSDT at 42500")
        assert result.order_type == "LIMIT"
