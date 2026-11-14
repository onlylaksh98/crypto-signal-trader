"""Pydantic schemas for RAG endpoints."""
from __future__ import annotations

import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Natural language question or search query")
    top_k: int = Field(5, ge=1, le=20, description="Number of context sources to retrieve")
    doc_type: Optional[str] = Field(None, description="Filter sources by doc_type (strategy, signal, risk_rule, channel)")
    symbol: Optional[str] = Field(None, description="Optional crypto symbol filter (e.g. ETH/USDT)")


class RagSourceRead(BaseModel):
    id: str
    title: str
    doc_type: str
    score: float
    match_type: str
    snippet: str
    metadata: dict[str, Any] = {}


class RagQueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[RagSourceRead]
    provider_used: str
    metrics: dict[str, Any]


class SignalEvaluateRequest(BaseModel):
    signal_id: Optional[uuid.UUID] = None
    symbol: Optional[str] = None
    direction: Optional[str] = None
    order_type: Optional[str] = "MARKET"
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    notes: Optional[str] = None


class SimilarTradeRead(BaseModel):
    signal_id: str
    symbol: str
    direction: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    outcome: str
    realized_pnl: Optional[float] = None
    realized_pnl_pct: Optional[float] = None
    similarity_score: float
    channel_name: str
    created_at: str
    notes: str


class SignalEvaluationResponse(BaseModel):
    symbol: str
    direction: str
    recommended_action: str
    confidence_score: float
    risk_score: int
    historical_win_rate_similar: float
    sample_size_similar: int
    evaluation_summary: str
    similar_trades: list[SimilarTradeRead]
    matched_strategies: list[str]
    actionable_advice: list[str]
    provider_used: str
    timestamp: str


class RagStatusResponse(BaseModel):
    provider: str
    gemini_configured: bool
    openai_configured: bool
    total_documents: int
    documents_by_type: dict[str, int]


class KnowledgeDocCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    doc_type: str = Field("strategy", description="strategy | risk_rule | channel")
    text: str = Field(..., min_length=20, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)
