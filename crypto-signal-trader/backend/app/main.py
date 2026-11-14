"""
CryptoSignal AI — Telegram Trading Terminal
FastAPI Application Entry Point

⚠️  PAPER TRADING ONLY — No real money orders are ever submitted.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.session import engine
from app.db.base import Base

configure_logging()
logger = get_logger(__name__)


# ── Application state container ──────────────────────────────────────────────

class AppState:
    def __init__(self) -> None:
        self.telegram_service = None
        self.market_data_service = None
        self._pnl_task = None
        self._ws_clients: list[WebSocket] = []


app_state = AppState()


# ── WebSocket broadcast helper ────────────────────────────────────────────────

async def broadcast_ws(data: dict) -> None:
    dead = []
    for ws in app_state._ws_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        app_state._ws_clients.remove(ws)


# ── Background task: update P&L every 30 seconds ─────────────────────────────

async def _pnl_updater() -> None:
    from app.db.session import AsyncSessionLocal
    from app.models.equity_snapshot import EquitySnapshot
    from app.services.portfolio_service import PortfolioService
    from app.services.risk_engine import RiskEngine
    from datetime import datetime, timezone

    logger.info("pnl_updater_started")
    while True:
        try:
            await asyncio.sleep(30)
            if app_state.market_data_service and app_state.market_data_service.is_connected:
                async with AsyncSessionLocal() as db:
                    ps = PortfolioService(db, app_state.market_data_service, RiskEngine())
                    await ps.update_unrealized_pnl()

                    # Take equity snapshot
                    from sqlalchemy import select
                    from app.models.portfolio import Portfolio

                    result = await db.execute(
                        select(Portfolio).where(Portfolio.is_default == True).limit(1)  # noqa
                    )
                    portfolio = result.scalar_one_or_none()
                    if portfolio:
                        snap = EquitySnapshot(
                            portfolio_id=portfolio.id,
                            timestamp=datetime.now(timezone.utc),
                            equity=portfolio.total_equity,
                            cash=portfolio.cash_balance,
                            unrealized_pnl=portfolio.unrealized_pnl,
                            realized_pnl=portfolio.realized_pnl,
                        )
                        db.add(snap)
                    await db.commit()
                    await broadcast_ws({"type": "pnl_update"})
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("pnl_updater_error", error=str(exc))


# ── Telegram → Signal pipeline handler ────────────────────────────────────────

async def _handle_telegram_message(channel_id: str, channel_name: str, text: str) -> None:
    """Process a raw Telegram message through the full signal pipeline:
    parse → validate → persist → execute paper trade."""
    from datetime import datetime, timezone as tz

    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.channel import TelegramChannel
    from app.models.message import TelegramMessage
    from app.models.signal import Signal
    from app.services.signal_parser import SignalParser
    from app.services.signal_validator import SignalValidator
    from app.services.portfolio_service import PortfolioService
    from app.services.risk_engine import RiskEngine

    parser = SignalParser()
    validator = SignalValidator()

    try:
        async with AsyncSessionLocal() as db:
            # 0. Resolve channel — TelegramMessage.channel_id is a UUID FK
            result = await db.execute(
                select(TelegramChannel).where(TelegramChannel.channel_id == channel_id)
            )
            db_channel = result.scalar_one_or_none()
            if db_channel is None:
                logger.warning("telegram_channel_not_found", channel_id=channel_id)
                return

            db_channel.messages_received += 1
            db_channel.last_message_at = datetime.now(tz.utc)

            # 1. Persist raw message
            msg = TelegramMessage(
                channel_id=db_channel.id,   # UUID PK of the channel
                message_id=0,               # Telegram message ID unknown at this layer
                sender_name=channel_name,
                raw_text=text,
                processed=True,
            )
            db.add(msg)

            # 2. Parse signal from text
            parsed = parser.parse(text)
            if not parsed.is_valid:
                msg.signal_parsed = False
                msg.parse_error = "Could not extract valid signal"
                db_channel.messages_rejected += 1
                await db.commit()
                return

            # 3. Validate against market data
            current_price = None
            if app_state.market_data_service and app_state.market_data_service.is_connected:
                current_price = await app_state.market_data_service.get_price(parsed.symbol)

            validation = validator.validate(parsed, current_price)
            if not validation.is_valid:
                msg.signal_parsed = False
                msg.parse_error = "; ".join(validation.errors)
                db_channel.messages_rejected += 1
                await db.commit()
                logger.warning("signal_validation_failed", errors=validation.errors)
                return

            msg.signal_parsed = True
            db_channel.messages_processed += 1
            db_channel.signals_parsed += 1

            # 3.5 RAG Historical Setup Enrichment & AI Risk Review
            rag_review_suffix = ""
            if settings.rag_auto_enrich_signals:
                try:
                    from app.services.rag.rag_service import rag_service
                    await rag_service.initialize()
                    rag_eval = await rag_service.evaluate_signal(
                        symbol=parsed.symbol,
                        direction=parsed.direction,
                        order_type=parsed.order_type,
                        entry_price=float(parsed.entry_price) if parsed.entry_price else None,
                        stop_loss=float(parsed.stop_loss) if parsed.stop_loss else None,
                        take_profit_1=float(parsed.take_profit_1) if parsed.take_profit_1 else None,
                        take_profit_2=float(parsed.take_profit_2) if parsed.take_profit_2 else None,
                        notes=text,
                    )
                    advice_str = "; ".join(rag_eval.actionable_advice[:2]) if rag_eval.actionable_advice else "Standard risk profile"
                    rag_review_suffix = f"\n[RAG AI Review]: Verdict={rag_eval.recommended_action} (Risk: {rag_eval.risk_score}/100, Win Rate on {rag_eval.sample_size_similar} similar: {rag_eval.historical_win_rate_similar}%). Advice: {advice_str}"
                except Exception as r_err:
                    logger.warning("rag_auto_enrich_error", error=str(r_err))

            # 4. Persist structured signal
            signal = Signal(
                source_message_id=msg.id,
                symbol=parsed.symbol,
                direction=parsed.direction,
                order_type=parsed.order_type,
                entry_price=parsed.entry_price,
                stop_loss=parsed.stop_loss,
                take_profit_1=parsed.take_profit_1,
                take_profit_2=parsed.take_profit_2,
                take_profit_3=parsed.take_profit_3,
                confidence_score=parsed.confidence_score,
                risk_reward_ratio=parsed.risk_reward_ratio,
                status="PENDING",
                raw_text=text,
                notes=f"Auto-parsed from channel {channel_name}{rag_review_suffix}",
            )
            db.add(signal)
            await db.flush()

            # 5. Execute paper trade
            if app_state.market_data_service and app_state.market_data_service.is_connected:
                ps = PortfolioService(db, app_state.market_data_service, RiskEngine())
                await ps.execute_signal(signal, parsed)

            await db.commit()

            # 6. Index in RAG vector store
            try:
                from app.services.rag.rag_service import rag_service
                await rag_service.index_signal(
                    signal_id=str(signal.id),
                    symbol=signal.symbol,
                    direction=signal.direction,
                    order_type=signal.order_type,
                    entry_price=float(signal.entry_price) if signal.entry_price else None,
                    stop_loss=float(signal.stop_loss) if signal.stop_loss else None,
                    take_profit_1=float(signal.take_profit_1) if signal.take_profit_1 else None,
                    take_profit_2=float(signal.take_profit_2) if signal.take_profit_2 else None,
                    confidence_score=float(signal.confidence_score) if signal.confidence_score else None,
                    risk_reward_ratio=float(signal.risk_reward_ratio) if signal.risk_reward_ratio else None,
                    notes=signal.notes,
                    status=signal.status,
                    channel_name=channel_name,
                )
            except Exception as r_idx_err:
                logger.warning("rag_index_signal_error", error=str(r_idx_err))

            await broadcast_ws({"type": "new_signal", "symbol": parsed.symbol})
            logger.info(
                "telegram_signal_processed",
                symbol=parsed.symbol,
                direction=parsed.direction,
                status=signal.status,
            )
    except Exception as exc:
        logger.error("telegram_pipeline_error", error=str(exc))


def _sync_message_handler(channel_id: str, channel_name: str, text: str) -> None:
    """Synchronous wrapper to schedule the async handler on the running loop."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_handle_telegram_message(channel_id, channel_name, text))
    except RuntimeError:
        logger.error("no_event_loop_for_telegram_handler")


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("startup", app_name=settings.app_name, paper_trading=settings.paper_trading_enabled)

    # DB tables (development convenience — use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Market data service
    from app.services.market_data_service import MarketDataService

    app_state.market_data_service = MarketDataService()
    await app_state.market_data_service.connect()

    # Telegram service (only if configured)
    if settings.telegram_configured:
        from app.services.telegram_service import TelegramService

        app_state.telegram_service = TelegramService()
        app_state.telegram_service.set_message_handler(_sync_message_handler)
        connected = await app_state.telegram_service.connect()
        if connected:
            asyncio.create_task(app_state.telegram_service.start_listening())

    # Initialize RAG Engine and index existing signals
    try:
        from app.services.rag.rag_service import rag_service
        from app.db.session import AsyncSessionLocal
        await rag_service.initialize()
        async with AsyncSessionLocal() as db:
            await rag_service.reindex_all_from_db(db)
        logger.info("rag_engine_started", documents_indexed=len(rag_service.vector_store.documents))
    except Exception as r_init_err:
        logger.warning("rag_init_warning", error=str(r_init_err))

    # Background P&L updater
    app_state._pnl_task = asyncio.create_task(_pnl_updater())

    logger.info("ready", telegram=bool(app_state.telegram_service and app_state.telegram_service.is_connected))

    yield

    # Cleanup
    if app_state._pnl_task:
        app_state._pnl_task.cancel()
    if app_state.telegram_service:
        await app_state.telegram_service.disconnect()
    if app_state.market_data_service:
        await app_state.market_data_service.close()
    await engine.dispose()
    logger.info("shutdown_complete")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="CryptoSignal AI — Telegram Trading Terminal",
    description="⚠️ PAPER TRADING ONLY. All trades are simulated.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "paper_trading": True,
        "telegram_connected": bool(
            app_state.telegram_service and app_state.telegram_service.is_connected
        ),
        "market_data_connected": bool(
            app_state.market_data_service and app_state.market_data_service.is_connected
        ),
        "version": "1.0.0",
    }


# ── WebSocket for real-time dashboard updates ─────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app_state._ws_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive ping
    except WebSocketDisconnect:
        app_state._ws_clients.remove(websocket)


# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("unhandled_exception", path=str(request.url), error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
