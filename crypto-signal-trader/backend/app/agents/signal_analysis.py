"""Signal Analysis Agent

Validates the structured `ParsedSignal` objects coming from the Telegram Monitoring Agent.
The agent checks:
* That a known trading pair / symbol is present.
* That direction is either BUY or SELL.
* That entry, stop‑loss and at least one take‑profit are numeric and sensible (stop < entry < tp for BUY, reverse for SELL).
* That leverage (if supplied in the raw text) does not exceed a configurable max.

Invalid or suspicious signals are logged and sent to a secondary "dead‑letter" queue for later review.
"""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import Optional

from app.services.signal_parser import ParsedSignal
from app.core.logging import get_logger

logger = get_logger(__name__)

# Simple in‑memory list of known base symbols – could later be loaded from DB or API.
KNOWN_BASES = {
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOT", "MATIC", "DOGE",
    "LTC", "LINK", "UNI", "AVAX", "ATOM",
}

MAX_LEVERAGE = 10  # configurable via env later

class SignalAnalysisError(RuntimeError):
    """Raised when a signal fails validation."""

class SignalAnalysisAgent:
    """Consumes `ParsedSignal` objects, validates them, and forwards valid ones.

    Parameters
    ----------
    in_queue: asyncio.Queue[ParsedSignal]
        Queue populated by the Telegram Monitoring Agent.
    out_queue: asyncio.Queue[ParsedSignal]
        Queue for downstream agents (Market Research, etc.).
    dead_letter: asyncio.Queue[ParsedSignal]
        Queue for signals that fail validation – useful for auditing.
    """

    def __init__(
        self,
        in_queue: asyncio.Queue[ParsedSignal],
        out_queue: asyncio.Queue[ParsedSignal],
        dead_letter: asyncio.Queue[ParsedSignal],
    ) -> None:
        self._in = in_queue
        self._out = out_queue
        self._dead = dead_letter
        self._running = False

    # ------------------------------------------------------------------
    def _validate_symbol(self, symbol: str) -> bool:
        # Accept explicit USDT pairs or base symbols that we know.
        if symbol.endswith("USDT"):
            base = symbol[:-4]
        else:
            base = symbol
        return base.upper() in KNOWN_BASES

    # ------------------------------------------------------------------
    def _validate_prices(self, signal: ParsedSignal) -> bool:
        if not signal.entry_price or not signal.stop_loss:
            return False
        if not signal.take_profits:
            return False
        # Ensure ordering based on direction.
        if signal.direction == "BUY":
            if not (signal.stop_loss < signal.entry_price <= signal.take_profits[0]):
                return False
        elif signal.direction == "SELL":
            if not (signal.entry_price <= signal.stop_loss and signal.entry_price >= signal.take_profits[0]):
                return False
        return True

    # ------------------------------------------------------------------
    def _extract_leverage(self, raw_text: str) -> Optional[int]:
        # Very simple regex to catch "leverage 5x" or "5x" patterns.
        import re
        m = re.search(r"(\d{1,2})x", raw_text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                return None
        return None

    # ------------------------------------------------------------------
    async def _process_signal(self, signal: ParsedSignal) -> None:
        try:
            # 1️⃣ Symbol check
            if not self._validate_symbol(signal.symbol):
                raise SignalAnalysisError(f"Unknown symbol {signal.symbol}")

            # 2️⃣ Direction must be BUY or SELL (already enforced by parser but double‑check)
            if signal.direction not in {"BUY", "SELL"}:
                raise SignalAnalysisError(f"Invalid direction {signal.direction}")

            # 3️⃣ Price sanity
            if not self._validate_prices(signal):
                raise SignalAnalysisError("Price relationship invalid")

            # 4️⃣ Leverage (optional)
            lev = self._extract_leverage(signal.raw_text)
            if lev is not None and lev > MAX_LEVERAGE:
                raise SignalAnalysisError(f"Leverage {lev} exceeds max {MAX_LEVERAGE}")

            # All good – forward downstream
            await self._out.put(signal)
            logger.info(
                "signal_validated",
                symbol=signal.symbol,
                direction=signal.direction,
                confidence=str(signal.confidence_score),
            )
        except SignalAnalysisError as exc:
            logger.warning(
                "signal_invalid",
                symbol=signal.symbol,
                error=str(exc),
                raw=signal.raw_text,
            )
            await self._dead.put(signal)
        except Exception as exc:
            logger.exception("signal_analysis_unexpected_error", error=str(exc))
            await self._dead.put(signal)

    # ------------------------------------------------------------------
    async def start(self) -> None:
        if self._running:
            logger.warning("SignalAnalysisAgent already running")
            return
        self._running = True
        logger.info("signal_analysis_agent_started")
        try:
            while self._running:
                signal: ParsedSignal = await self._in.get()
                await self._process_signal(signal)
                self._in.task_done()
        finally:
            self._running = False
            logger.info("signal_analysis_agent_stopped")

    async def stop(self) -> None:
        self._running = False
        logger.info("signal_analysis_agent_stop_requested")

