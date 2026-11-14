"""
Telegram Service
----------------
Manages the Telethon client: connecting, listening to channels,
and forwarding raw messages to the signal pipeline.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Callable, Optional

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import Message

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

MessageHandler = Callable[[str, str, str], None]


class TelegramService:
    """
    Wraps Telethon client for channel monitoring.
    Emits raw (channel_id, channel_name, text) tuples via a callback.
    """

    def __init__(self) -> None:
        self._client: Optional[TelegramClient] = None
        self._connected = False
        self._monitored_channels: set[str] = set()
        self._message_handler: Optional[MessageHandler] = None
        self._message_count = 0
        self._last_error: Optional[str] = None

    def set_message_handler(self, handler: MessageHandler) -> None:
        self._message_handler = handler

    async def connect(self) -> bool:
        """Initialize the Telegram client and attempt to reuse a saved session.
        Returns ``True`` if the client is already authorized; otherwise ``False``.
        No interactive OTP/2FA prompt is performed here – authentication is handled
        separately via :meth:`authorize`.
        """
        if not settings.telegram_configured:
            logger.warning("telegram_not_configured")
            return False
        try:
            session = StringSession(settings.telegram_session_string or "")
            self._client = TelegramClient(
                session,
                settings.telegram_api_id,
                settings.telegram_api_hash,
            )
            await self._client.connect()
            self._connected = await self._client.is_user_authorized()
            if self._connected:
                logger.info("telegram_connected")
            else:
                logger.info("telegram_not_authorized")
            return self._connected
        except Exception as exc:
            self._last_error = str(exc)
            self._connected = False
            logger.error("telegram_connect_failed", error=str(exc))
            return False

    async def authorize(self, phone: str, code: str, password: Optional[str] = None) -> bool:
        """Authorize the Telegram client using provided credentials.

        Parameters
        ----------
        phone: str – phone number in international format.
        code: str – OTP code received from Telegram.
        password: Optional[str] – 2FA password if enabled.
        """
        if not self._client:
            raise RuntimeError("Telegram client not initialized. Call `connect` first.")
        try:
            def sync_code_callback() -> str:
                return code

            def sync_password_callback() -> Optional[str]:
                return password

            await self._client.start(
                phone=phone,
                code_callback=sync_code_callback,
                password=sync_password_callback() if password else None,
            )
            from app.core.config import settings
            settings.telegram_session_string = self._client.session.save()
            self._connected = True
            logger.info("telegram_connected_after_auth")
            return True
        except Exception as exc:
            self._last_error = str(exc)
            self._connected = False
            logger.error("telegram_auth_failed", error=str(exc))
            return False


    async def authorize(self, phone: str, code: str, password: Optional[str] = None) -> bool:
        """Authorize the Telegram client using provided credentials.

        Parameters
        ----------
        phone: str – phone number in international format.
        code: str – OTP code received from Telegram.
        password: Optional[str] – 2FA password if enabled.
        """
        if not self._client:
            raise RuntimeError("Telegram client not initialized. Call `connect` first.")
        try:
            def sync_code_callback() -> str:
                return code

            def sync_password_callback() -> Optional[str]:
                return password

            await self._client.start(
                phone=phone,
                code_callback=sync_code_callback,
                password=sync_password_callback() if password else None,
            )
            from app.core.config import settings
            settings.telegram_session_string = self._client.session.save()
            self._connected = True
            logger.info("telegram_connected_after_auth")
            return True
        except Exception as exc:
            self._last_error = str(exc)
            self._connected = False
            logger.error("telegram_auth_failed", error=str(exc))
            return False


        except Exception as exc:
            self._last_error = str(exc)
            self._connected = False
            logger.error("telegram_connect_failed", error=str(exc))
            return False

    async def authorize(self, phone: str, code: str, password: Optional[str] = None) -> bool:
        """Authorize the Telegram client using provided credentials.

        Parameters
        ----------
        phone: str – phone number in international format.
        code: str – OTP code received from Telegram.
        password: Optional[str] – 2FA password if enabled.
        """
        if not self._client:
            raise RuntimeError("Telegram client not initialized. Call `connect` first.")
        try:
            def sync_code_callback() -> str:
                return code

            def sync_password_callback() -> Optional[str]:
                return password

            await self._client.start(
                phone=phone,
                code_callback=sync_code_callback,
                password=sync_password_callback() if password else None,
            )
            from app.core.config import settings
            settings.telegram_session_string = self._client.session.save()
            self._connected = True
            logger.info("telegram_connected_after_auth")
            return True
        except Exception as exc:
            self._last_error = str(exc)
            self._connected = False
            logger.error("telegram_auth_failed", error=str(exc))
            return False

    async def disconnect(self) -> None:
        if self._client:
            await self._client.disconnect()
        self._connected = False

    async def add_channel(self, channel_identifier: str) -> dict:
        """
        Resolves a channel username / ID and starts monitoring it.
        Returns channel metadata.
        """
        if not self._client or not self._connected:
            raise RuntimeError("Telegram client not connected")

        try:
            entity = await self._client.get_entity(channel_identifier)
            channel_id = str(entity.id)
            self._monitored_channels.add(channel_id)

            title = getattr(entity, "title", None)
            username = getattr(entity, "username", None)

            logger.info("channel_added", channel_id=channel_id, title=title)
            return {
                "channel_id": channel_id,
                "channel_title": title,
                "channel_username": username,
            }
        except Exception as exc:
            logger.error("add_channel_failed", identifier=channel_identifier, error=str(exc))
            raise

    def remove_channel(self, channel_id: str) -> None:
        self._monitored_channels.discard(channel_id)
        logger.info("channel_removed", channel_id=channel_id)

    async def start_listening(self) -> None:
        """Registers the Telethon event handler and keeps the client running."""
        if not self._client or not self._connected:
            logger.warning("telegram_listen_skipped_not_connected")
            return

        @self._client.on(events.NewMessage())
        async def _handler(event: events.NewMessage.Event) -> None:
            try:
                chat = await event.get_chat()
                chat_id = str(chat.id)

                if chat_id not in self._monitored_channels:
                    return

                message: Message = event.message
                if not message.text:
                    return

                self._message_count += 1
                logger.debug(
                    "telegram_message_received",
                    chat_id=chat_id,
                    message_id=message.id,
                )

                if self._message_handler:
                    self._message_handler(
                        chat_id,
                        getattr(chat, "username", None) or chat_id,
                        message.text,
                    )
            except Exception as exc:
                logger.error("telegram_handler_error", error=str(exc))

        await self._client.run_until_disconnected()

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def monitored_channel_ids(self) -> set[str]:
        return self._monitored_channels.copy()

    @property
    def message_count(self) -> int:
        return self._message_count

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error
