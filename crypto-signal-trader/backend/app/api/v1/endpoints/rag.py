"""
RAG & AI Copilot Endpoints
--------------------------
API routes for interactive chat queries, contextual signal evaluations,
knowledge base document management, and vector store reindexing.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import get_db
from app.models.signal import Signal
from app.schemas.rag import (
    KnowledgeDocCreate,
    RagQueryRequest,
    RagQueryResponse,
    RagSourceRead,
    RagStatusResponse,
    SignalEvaluateRequest,
    SignalEvaluationResponse,
    SimilarTradeRead,
)
from app.services.rag.models import Document
from app.services.rag.rag_service import rag_service

router = APIRouter()


@router.get("/status", response_model=RagStatusResponse)
async def get_rag_status():
    """Returns current RAG engine status, document statistics, and active LLM provider."""
    # Ensure initialized
    await rag_service.initialize()
    counts = rag_service.vector_store.count_by_type()
    return RagStatusResponse(
        provider=rag_service.embedding_engine.provider,
        gemini_configured=bool(settings.gemini_api_key),
        openai_configured=bool(settings.openai_api_key),
        total_documents=len(rag_service.vector_store.documents),
        documents_by_type=counts,
    )


@router.post("/query", response_model=RagQueryResponse)
async def query_copilot(payload: RagQueryRequest):
    """
    Interactive natural-language query to AI Trading Copilot.
    Retrieves grounded context from historical signals and strategy documents.
    """
    await rag_service.initialize()
    result = await rag_service.query(
        query_text=payload.query,
        top_k=payload.top_k,
        doc_type=payload.doc_type,
        symbol=payload.symbol,
    )
    return RagQueryResponse(
        query=result["query"],
        answer=result["answer"],
        sources=[RagSourceRead(**s) for s in result["sources"]],
        provider_used=result["provider_used"],
        metrics=result["metrics"],
    )


@router.post("/evaluate", response_model=SignalEvaluationResponse)
async def evaluate_signal(
    payload: SignalEvaluateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates a specific trading signal using RAG.
    Can accept an existing signal_id OR raw parameters for simulated signals.
    """
    await rag_service.initialize()

    symbol = payload.symbol
    direction = payload.direction
    order_type = payload.order_type or "MARKET"
    entry_price = payload.entry_price
    stop_loss = payload.stop_loss
    take_profit_1 = payload.take_profit_1
    take_profit_2 = payload.take_profit_2
    take_profit_3 = payload.take_profit_3
    notes = payload.notes

    if payload.signal_id:
        result = await db.execute(select(Signal).where(Signal.id == payload.signal_id))
        sig = result.scalar_one_or_none()
        if not sig:
            raise HTTPException(status_code=404, detail="Signal not found")
        symbol = sig.symbol
        direction = sig.direction
        order_type = sig.order_type
        entry_price = float(sig.entry_price) if sig.entry_price else None
        stop_loss = float(sig.stop_loss) if sig.stop_loss else None
        take_profit_1 = float(sig.take_profit_1) if sig.take_profit_1 else None
        take_profit_2 = float(sig.take_profit_2) if sig.take_profit_2 else None
        take_profit_3 = float(sig.take_profit_3) if sig.take_profit_3 else None
        notes = sig.notes or sig.raw_text

    if not symbol or not direction:
        raise HTTPException(
            status_code=400,
            detail="Either signal_id or both symbol and direction must be provided",
        )

    res = await rag_service.evaluate_signal(
        symbol=symbol,
        direction=direction,
        order_type=order_type,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit_1=take_profit_1,
        take_profit_2=take_profit_2,
        take_profit_3=take_profit_3,
        notes=notes,
    )

    return SignalEvaluationResponse(
        symbol=res.symbol,
        direction=res.direction,
        recommended_action=res.recommended_action,
        confidence_score=res.confidence_score,
        risk_score=res.risk_score,
        historical_win_rate_similar=res.historical_win_rate_similar,
        sample_size_similar=res.sample_size_similar,
        evaluation_summary=res.evaluation_summary,
        similar_trades=[
            SimilarTradeRead(
                signal_id=t.signal_id,
                symbol=t.symbol,
                direction=t.direction,
                entry_price=t.entry_price,
                stop_loss=t.stop_loss,
                take_profit=t.take_profit,
                outcome=t.outcome,
                realized_pnl=t.realized_pnl,
                realized_pnl_pct=t.realized_pnl_pct,
                similarity_score=t.similarity_score,
                channel_name=t.channel_name,
                created_at=t.created_at,
                notes=t.notes,
            )
            for t in res.similar_trades
        ],
        matched_strategies=res.matched_strategies,
        actionable_advice=res.actionable_advice,
        provider_used=res.provider_used,
        timestamp=res.timestamp,
    )


@router.get("/knowledge-base")
async def list_knowledge_docs(doc_type: str | None = None):
    """Lists indexed documents in the knowledge base and vector store."""
    await rag_service.initialize()
    docs = rag_service.vector_store.list_all(doc_type=doc_type)
    return [
        {
            "id": d.id,
            "title": d.title,
            "doc_type": d.doc_type,
            "text": d.text,
            "metadata": d.metadata,
            "created_at": d.created_at,
            "has_embedding": bool(d.embedding),
        }
        for d in docs
    ]


@router.post("/knowledge-base", status_code=201)
async def add_knowledge_doc(payload: KnowledgeDocCreate):
    """Add a custom trading playbook or risk rule to the RAG vector store."""
    await rag_service.initialize()
    vec, _ = await rag_service.embedding_engine.get_embedding(f"{payload.title}\n{payload.text}")
    doc = Document(
        id=f"kb-custom-{uuid.uuid4().hex[:8]}",
        title=payload.title,
        doc_type=payload.doc_type,
        text=payload.text,
        metadata=payload.metadata,
        embedding=vec,
    )
    rag_service.vector_store.add(doc)
    rag_service.vector_store.save()
    return {"message": "Document indexed successfully", "document_id": doc.id}


@router.post("/reindex")
async def reindex_signals(db: AsyncSession = Depends(get_db)):
    """Triggers reindexing of all historical signals and positions from DB into the vector store."""
    await rag_service.initialize()
    count = await rag_service.reindex_all_from_db(db)
    return {
        "message": "Reindexing complete",
        "signals_indexed": count,
        "total_documents": len(rag_service.vector_store.documents),
    }
