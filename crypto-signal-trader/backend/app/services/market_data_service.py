"""
Market Data Service
-------------------
Fetches public ticker/OHLCV data via CCXT (no private keys needed).
Handles retries, rate limiting, and graceful degradation.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Optional

# pyrefly: ignore [missing-import]
import ccxt.async_support as ccxt
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MarketDataService:
    """
    Wraps CCXT for public market data retrieval.
    Fully independent — can be tested with a mock exchange.
    """

    def __init__(self, exchange_id: str | None = None) -> None:
        eid = exchange_id or settings.market_data_exchange
        exchange_class = getattr(ccxt, eid, None)
        if exchange_class is None:
            raise ValueError(f"Unknown CCXT exchange: {eid}")
        self._exchange: ccxt.Exchange = exchange_class(
            {"timeout": settings.market_data_timeout_ms}
        )
        self._exchange_id = eid
        self._connected = False

    async def connect(self) -> None:
        try:
            await self._exchange.load_markets()
            self._connected = True
            logger.info("market_data_connected", exchange=self._exchange_id)
        except Exception as exc:
            logger.error("market_data_connect_failed", exchange=self._exchange_id, error=str(exc))
            self._connected = False

    async def close(self) -> None:
        await self._exchange.close()
        self._connected = False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def get_price(self, symbol: str) -> Optional[Decimal]:
        """
        Returns the last traded price for a symbol (e.g. 'BTC/USDT').
        Returns None if the market is unavailable.
        """
        try:
            ccxt_symbol = self._normalize_symbol(symbol)
            ticker = await self._exchange.fetch_ticker(ccxt_symbol)
            price = ticker.get("last") or ticker.get("close")
            if price is None:
                return None
            return Decimal(str(price))
        except ccxt.BadSymbol:
            logger.warning("bad_symbol", symbol=symbol)
            return None
        except Exception as exc:
            logger.error("fetch_ticker_failed", symbol=symbol, error=str(exc))
            raise

    async def get_prices_batch(self, symbols: list[str]) -> dict[str, Optional[Decimal]]:
        """Fetch multiple prices concurrently."""
        tasks = [self.get_price(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out: dict[str, Optional[Decimal]] = {}
        for sym, res in zip(symbols, results):
            if isinstance(res, Exception):
                out[sym] = None
            else:
                out[sym] = res
        return out

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
    ) -> list[dict]:
        """Returns list of {timestamp, open, high, low, close, volume}."""
        try:
            ccxt_symbol = self._normalize_symbol(symbol)
            raw = await self._exchange.fetch_ohlcv(ccxt_symbol, timeframe, limit=limit)
            return [
                {
                    "timestamp": candle[0],
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5],
                }
                for candle in raw
            ]
        except Exception as exc:
            logger.error("fetch_ohlcv_failed", symbol=symbol, error=str(exc))
            return []

    @property
    def is_connected(self) -> bool:
        return self._connected

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Convert 'BTCUSDT' → 'BTC/USDT' for CCXT."""
        if "/" in symbol:
            return symbol.upper()
        for quote in ("USDT", "BTC", "ETH", "BNB", "BUSD"):
            if symbol.upper().endswith(quote):
                base = symbol.upper()[: -len(quote)]
                return f"{base}/{quote}"
        return symbol.upper()
