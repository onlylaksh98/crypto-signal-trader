"""
RAG (Retrieval-Augmented Generation) Data Models
------------------------------------------------
Defines document structures, search results, evaluation responses,
and context representation for trading signals and strategy knowledge.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class Document:
    """A single chunk or item stored in the RAG vector/hybrid index."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    doc_type: str = "strategy"  # "strategy" | "signal" | "channel" | "risk_rule"
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "doc_type": self.doc_type,
            "title": self.title,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            text=data.get("text", ""),
            doc_type=data.get("doc_type", "strategy"),
            title=data.get("title", ""),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding", []),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class SearchResult:
    """Ranked document match returned by the hybrid retrieval engine."""
    document: Document
    score: float  # Normalized 0.0 to 1.0
    match_type: str = "hybrid"  # "semantic" | "keyword" | "hybrid"
    keyword_score: float = 0.0
    vector_score: float = 0.0


@dataclass
class SimilarTrade:
    """Historical trade representation extracted for contextual comparison."""
    signal_id: str
    symbol: str
    direction: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    outcome: str  # "WIN" | "LOSS" | "OPEN" | "REJECTED"
    realized_pnl: Optional[float]
    realized_pnl_pct: Optional[float]
    similarity_score: float
    channel_name: str
    created_at: str
    notes: str


@dataclass
class SignalEvaluationResult:
    """AI + RAG evaluation for a specific trading signal."""
    symbol: str
    direction: str
    recommended_action: str  # "EXECUTE" | "CAUTION" | "REJECT"
    confidence_score: float  # 0.0 - 1.0
    risk_score: int  # 0 (safe) - 100 (extreme risk)
    historical_win_rate_similar: float  # percentage e.g. 75.0
    sample_size_similar: int
    evaluation_summary: str
    similar_trades: list[SimilarTrade] = field(default_factory=list)
    matched_strategies: list[str] = field(default_factory=list)
    actionable_advice: list[str] = field(default_factory=list)
    provider_used: str = "local"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "recommended_action": self.recommended_action,
            "confidence_score": round(self.confidence_score, 3),
            "risk_score": self.risk_score,
            "historical_win_rate_similar": round(self.historical_win_rate_similar, 1),
            "sample_size_similar": self.sample_size_similar,
            "evaluation_summary": self.evaluation_summary,
            "similar_trades": [
                {
                    "signal_id": t.signal_id,
                    "symbol": t.symbol,
                    "direction": t.direction,
                    "entry_price": t.entry_price,
                    "stop_loss": t.stop_loss,
                    "take_profit": t.take_profit,
                    "outcome": t.outcome,
                    "realized_pnl": t.realized_pnl,
                    "realized_pnl_pct": t.realized_pnl_pct,
                    "similarity_score": round(t.similarity_score, 3),
                    "channel_name": t.channel_name,
                    "created_at": t.created_at,
                    "notes": t.notes,
                }
                for t in self.similar_trades
            ],
            "matched_strategies": self.matched_strategies,
            "actionable_advice": self.actionable_advice,
            "provider_used": self.provider_used,
            "timestamp": self.timestamp,
        }
