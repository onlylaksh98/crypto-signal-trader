"""
Signal Parser Service
---------------------
Extracts structured trading instructions from raw Telegram message text.
Uses regex pattern matching with a confidence scoring system.
Entirely deterministic — no external calls.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Regex patterns ────────────────────────────────────────────────────────────

_SYMBOL_PAT = re.compile(
    r"\b([A-Z]{2,10}(?:USDT|BTC|ETH|BNB|USD|BUSD)?)\b", re.IGNORECASE
)
_BUY_PAT = re.compile(r"\b(buy|long|bullish|call)\b", re.IGNORECASE)
_SELL_PAT = re.compile(r"\b(sell|short|bearish|put)\b", re.IGNORECASE)
_ENTRY_PAT = re.compile(
    r"(?:entry|enter|buy\s+at|sell\s+at|price)[:\s]+(\d[\d,\.]+)", re.IGNORECASE
)
_SL_PAT = re.compile(
    r"(?:stop[\s-]?loss|sl|stop)[:\s]+(\d[\d,\.]+)", re.IGNORECASE
)
_TP_PAT = re.compile(
    r"(?:take[\s-]?profit|tp|target)[\s#]*(\d?)[:\s]+(\d[\d,\.]+)", re.IGNORECASE
)
_MARKET_PAT = re.compile(r"\b(market\s+order|market|at\s+market)\b", re.IGNORECASE)
_LIMIT_PAT = re.compile(r"\b(limit\s+order|limit)\b", re.IGNORECASE)

# Common crypto pairs — used for symbol disambiguation
KNOWN_BASES = {
    "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "MATIC",
    "LINK", "UNI", "AVAX", "ATOM", "LTC", "TRX", "NEAR", "FTM", "SAND",
    "MANA", "ALGO", "VET", "FIL", "ICP", "EOS", "AAVE", "MKR", "COMP",
    "SNX", "SUSHI", "1INCH", "ENJ", "CHZ", "ROSE", "ONE", "ZIL", "HOT",
}


def _clean_number(s: str) -> Optional[Decimal]:
    cleaned = s.replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


@dataclass
class ParsedSignal:
    symbol: str = ""
    direction: str = ""          # BUY | SELL
    order_type: str = "MARKET"   # MARKET | LIMIT
    entry_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profits: list[Decimal] = field(default_factory=list)
    confidence_score: Decimal = Decimal("0")
    notes: list[str] = field(default_factory=list)
    raw_text: str = ""

    @property
    def is_valid(self) -> bool:
        return bool(self.symbol and self.direction)

    @property
    def take_profit_1(self) -> Optional[Decimal]:
        return self.take_profits[0] if len(self.take_profits) > 0 else None

    @property
    def take_profit_2(self) -> Optional[Decimal]:
        return self.take_profits[1] if len(self.take_profits) > 1 else None

    @property
    def take_profit_3(self) -> Optional[Decimal]:
        return self.take_profits[2] if len(self.take_profits) > 2 else None

    @property
    def risk_reward_ratio(self) -> Optional[Decimal]:
        if self.entry_price and self.stop_loss and self.take_profits:
            risk = abs(self.entry_price - self.stop_loss)
            reward = abs(self.take_profits[0] - self.entry_price)
            if risk > 0:
                return round(reward / risk, 4)
        return None


class SignalParser:
    """
    Parses raw text messages into structured ParsedSignal objects.
    Fully independent of any database or external service.
    """

    def parse(self, text: str) -> ParsedSignal:
        signal = ParsedSignal(raw_text=text)
        text_upper = text.upper()
        score = Decimal("0")

        # ── Symbol extraction ────────────────────────────────────────────────
        symbols = _SYMBOL_PAT.findall(text_upper)
        for sym in symbols:
            base = sym.replace("USDT", "").replace("BTC", "").replace("ETH", "")
            if base in KNOWN_BASES or sym.endswith("USDT"):
                candidate = sym if sym.endswith(("USDT", "BTC", "ETH")) else f"{sym}USDT"
                signal.symbol = candidate.upper()
                score += Decimal("20")
                break

        # ── Direction ────────────────────────────────────────────────────────
        buy_match = _BUY_PAT.search(text)
        sell_match = _SELL_PAT.search(text)
        if buy_match and not sell_match:
            signal.direction = "BUY"
            score += Decimal("20")
        elif sell_match and not buy_match:
            signal.direction = "SELL"
            score += Decimal("20")
        elif buy_match and sell_match:
            # Ambiguous — pick whichever appears first
            if buy_match.start() < sell_match.start():
                signal.direction = "BUY"
            else:
                signal.direction = "SELL"
            score += Decimal("10")
            signal.notes.append("Direction ambiguous — both BUY and SELL keywords found")

        # ── Order type ───────────────────────────────────────────────────────
        if _MARKET_PAT.search(text):
            signal.order_type = "MARKET"
        elif _LIMIT_PAT.search(text):
            signal.order_type = "LIMIT"
        else:
            signal.order_type = "MARKET"  # default

        # ── Entry price ──────────────────────────────────────────────────────
        entry_m = _ENTRY_PAT.search(text)
        if entry_m:
            val = _clean_number(entry_m.group(1))
            if val and val > 0:
                signal.entry_price = val
                score += Decimal("15")

        # ── Stop loss ────────────────────────────────────────────────────────
        sl_m = _SL_PAT.search(text)
        if sl_m:
            val = _clean_number(sl_m.group(1))
            if val and val > 0:
                signal.stop_loss = val
                score += Decimal("15")

        # ── Take profits ─────────────────────────────────────────────────────
        tps: dict[int, Decimal] = {}
        for m in _TP_PAT.finditer(text):
            idx_str = m.group(1)
            idx = int(idx_str) if idx_str else len(tps) + 1
            val = _clean_number(m.group(2))
            if val and val > 0:
                tps[idx] = val

        for k in sorted(tps.keys()):
            signal.take_profits.append(tps[k])
        if signal.take_profits:
            score += Decimal("10") * min(len(signal.take_profits), 3)

        signal.confidence_score = min(score, Decimal("100"))

        logger.debug(
            "signal_parsed",
            symbol=signal.symbol,
            direction=signal.direction,
            confidence=str(signal.confidence_score),
        )
        return signal
