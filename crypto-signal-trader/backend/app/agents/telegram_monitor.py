// backend/app/agents/telegram_monitor.py
"""Telegram Monitoring Agent

Continuously monitors the configured Telegram channels, parses incoming messages into
structured `ParsedSignal` objects (using existing `SignalParser`), and places the
signals onto an async queue for downstream agents.

The agent is deliberately lightweight: it does not perform any I/O besides
reading from the Telethon client and pushing to the queue. All error handling
and logging is performed via the project's standard logger.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.services.telegram_service import TelegramService
from app.services.signal_parser import SignalParser, ParsedSignal

logger = logging.getLogger(__name__)


class TelegramMonitoringAgent:
    """Agent that watches Telegram channels and emits parsed signals.

    Parameters
    ----------
    service: TelegramService
        Pre‑initialised service (must be connected/authorized).
    parser: SignalParser
        Re‑usable parser that converts raw text into :class:`ParsedSignal`.
    out_queue: asyncio.Queue[ParsedSignal]
        Queue onto which parsed signals are placed.
    """

    def __init__(
        self,
        service: TelegramService,
        parser: SignalParser,
        out_queue: asyncio.Queue[ParsedSignal],
    ) -> None:
        self._service = service
        self._parser = parser
        self._out_queue = out_queue
        self._running = False

    async def _handle_message(self, chat_id: str, chat_name: str, text: str) -> None:
        """Parse a raw Telegram message and push the result to the queue.

        Errors in parsing are logged but do not stop the agent – a malformed
        message simply results in no signal being emitted.
        """
        try:
            signal: ParsedSignal = self._parser.parse(text)
            if signal.is_valid:
                await self._out_queue.put(signal)
                logger.info(
                    "telegram_signal_parsed",
                    chat_id=chat_id,
                    chat_name=chat_name,
                    symbol=signal.symbol,
                    direction=signal.direction,
                    confidence=str(signal.confidence_score),
                )
            else:
                logger.debug(
                    "telegram_signal_invalid",
                    chat_id=chat_id,
                    chat_name=chat_name,
                    raw=text,
                )
        except Exception as exc:
            logger.exception(
                "telegram_signal_processing_error",
                chat_id=chat_id,
                chat_name=chat_name,
                error=str(exc),
            )

    async def start(self) -> None:
        """Start the monitoring loop.

        Registers the internal message handler with the ``TelegramService`` and
        then runs the Telethon client until a disconnect is requested.
        """
        if self._running:
            logger.warning("TelegramMonitoringAgent already running")
            return
        self._running = True

        # Register the callback that will be called for each new Telegram message.
        self._service.set_message_handler(self._handle_message)

        logger.info("telegram_monitor_agent_starting")
        try:
            await self._service.start_listening()
        finally:
            self._running = False
            logger.info("telegram_monitor_agent_stopped")

    async def stop(self) -> None:
        """Gracefully stop the agent by disconnecting the Telegram client."""
        if not self._running:
            return
        await self._service.disconnect()
        self._running = False
        logger.info("telegram_monitor_agent_requested_stop")

