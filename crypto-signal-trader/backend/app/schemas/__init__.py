"""Pydantic v2 schemas for all API requests and responses."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Common ─────────────────────────────────────────────────────────────────

class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Portfolio ───────────────────────────────────────────────────────────────

class PortfolioRead(OrmBase):
    id: uuid.UUID
    name: str
    currency: str
    initial_balance: Decimal
    cash_balance: Decimal
    total_equity: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    daily_pnl: Decimal
    max_drawdown: Decimal
    peak_equity: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    created_at: datetime
    updated_at: datetime


# ── Equity Snapshots ─────────────────────────────────────────────────────────

class EquitySnapshotRead(OrmBase):
    id: uuid.UUID
    timestamp: datetime
    equity: Decimal
    cash: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal


# ── Signal ──────────────────────────────────────────────────────────────────

class SignalRead(OrmBase):
    id: uuid.UUID
    symbol: str
    exchange: str
    direction: str
    order_type: str
    entry_price: Optional[Decimal]
    stop_loss: Optional[Decimal]
    take_profit_1: Optional[Decimal]
    take_profit_2: Optional[Decimal]
    take_profit_3: Optional[Decimal]
    risk_reward_ratio: Optional[Decimal]
    confidence_score: Optional[Decimal]
    status: str
    validation_errors: Optional[str]
    raw_text: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class SignalCreate(BaseModel):
    symbol: str
    direction: str
    order_type: str = "MARKET"
    entry_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit_1: Optional[Decimal] = None
    take_profit_2: Optional[Decimal] = None
    take_profit_3: Optional[Decimal] = None
    notes: Optional[str] = None


# ── Position ────────────────────────────────────────────────────────────────

class PositionRead(OrmBase):
    id: uuid.UUID
    symbol: str
    direction: str
    status: str
    entry_price: Decimal
    exit_price: Optional[Decimal]
    quantity: Decimal
    notional_value: Decimal
    stop_loss: Optional[Decimal]
    take_profit_1: Optional[Decimal]
    take_profit_2: Optional[Decimal]
    take_profit_3: Optional[Decimal]
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    fees_paid: Decimal
    opened_at: Optional[datetime]
    closed_at: Optional[datetime]
    close_reason: Optional[str]
    created_at: datetime


# ── Order ────────────────────────────────────────────────────────────────────

class OrderRead(OrmBase):
    id: uuid.UUID
    symbol: str
    side: str
    order_type: str
    status: str
    execution_mode: str       # Always "PAPER"
    requested_quantity: Decimal
    filled_quantity: Decimal
    requested_price: Optional[Decimal]
    filled_price: Optional[Decimal]
    slippage_bps: int
    fee: Decimal
    notes: Optional[str]
    created_at: datetime


# ── Telegram Channel ─────────────────────────────────────────────────────────

class ChannelRead(OrmBase):
    id: uuid.UUID
    channel_id: str
    channel_username: Optional[str]
    channel_title: Optional[str]
    is_active: bool
    is_monitored: bool
    messages_received: int
    messages_processed: int
    messages_rejected: int
    signals_parsed: int
    last_message_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime


class ChannelCreate(BaseModel):
    channel_identifier: str = Field(description="Channel username (e.g. @channelname) or numeric ID")


class ChannelUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_monitored: Optional[bool] = None


# ── Telegram Message ─────────────────────────────────────────────────────────

class MessageRead(OrmBase):
    id: uuid.UUID
    channel_id: uuid.UUID
    message_id: int
    sender_name: Optional[str]
    raw_text: str
    processed: bool
    signal_parsed: bool
    parse_error: Optional[str]
    created_at: datetime


# ── Dashboard / Overview ─────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    portfolio: PortfolioRead
    open_positions_count: int
    recent_signals: list[SignalRead]
    recent_orders: list[OrderRead]
    equity_curve: list[EquitySnapshotRead]
    telegram_connected: bool
    market_data_connected: bool
    is_paper_trading: bool = True


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    paper_trading: bool
    telegram_connected: bool
    market_data_connected: bool
    version: str = "1.0.0"


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int


# ── RAG & AI Copilot ──────────────────────────────────────────────────────────

from app.schemas.rag import (
    RagQueryRequest,
    RagQueryResponse,
    RagSourceRead,
    SignalEvaluateRequest,
    SignalEvaluationResponse,
    SimilarTradeRead,
    RagStatusResponse,
    KnowledgeDocCreate,
)
