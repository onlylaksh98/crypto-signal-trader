"""
Core RAG Service Orchestrator
-----------------------------
Coordinates hybrid indexing, dense embeddings, vector retrieval,
signal historical comparisons, and LLM response generation.
"""
from __future__ import annotations

import time
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging import get_logger
from app.services.rag.embeddings import EmbeddingEngine
from app.services.rag.knowledge_base import DEFAULT_KNOWLEDGE_DOCUMENTS
from app.services.rag.llm_client import LLMDispatcher
from app.services.rag.models import (
    Document,
    SearchResult,
    SignalEvaluationResult,
    SimilarTrade,
)
from app.services.rag.vector_store import HybridVectorStore

logger = get_logger(__name__)


class RagService:
    """Enterprise RAG Service for Crypto Trading Terminal."""

    def __init__(self) -> None:
        self.vector_store = HybridVectorStore()
        self.embedding_engine = EmbeddingEngine()
        self.llm_dispatcher = LLMDispatcher()
        self._initialized = False

    async def initialize(self) -> None:
        """Seed default knowledge base documents into vector store if missing."""
        if self._initialized:
            return

        logger.info("rag_service_initializing")
        for doc in DEFAULT_KNOWLEDGE_DOCUMENTS:
            existing = self.vector_store.get(doc.id)
            if not existing or not existing.embedding:
                vec, _ = await self.embedding_engine.get_embedding(f"{doc.title}\n{doc.text}")
                doc.embedding = vec
                self.vector_store.add(doc)

        self.vector_store.save()
        self._initialized = True
        logger.info(
            "rag_service_ready",
            total_documents=len(self.vector_store.documents),
            breakdown=self.vector_store.count_by_type(),
            provider=self.embedding_engine.provider,
        )

    async def index_signal(
        self,
        signal_id: str,
        symbol: str,
        direction: str,
        order_type: str,
        entry_price: Optional[float],
        stop_loss: Optional[float],
        take_profit_1: Optional[float],
        take_profit_2: Optional[float],
        confidence_score: Optional[float] = None,
        risk_reward_ratio: Optional[float] = None,
        notes: Optional[str] = None,
        status: str = "PENDING",
        outcome: str = "PENDING",
        realized_pnl: float = 0.0,
        channel_name: str = "Telegram",
        created_at: Optional[str] = None,
    ) -> Document:
        """Indexes or updates a trading signal into the vector store."""
        rr_str = f"1:{risk_reward_ratio:.2f}" if risk_reward_ratio else "N/A"
        text = (
            f"Trading Signal: {symbol} {direction} {order_type}. "
            f"Entry Price: {entry_price or 'Market'}, Stop Loss: {stop_loss or 'None'}, "
            f"TP1: {take_profit_1 or 'None'}, TP2: {take_profit_2 or 'None'}. "
            f"Risk:Reward: {rr_str}. Confidence: {confidence_score or 0}%. "
            f"Status: {status}. Outcome: {outcome}. Realized PnL: ${realized_pnl:+.2f}. "
            f"Source Channel: {channel_name}. Notes: {notes or 'No notes provided.'}"
        )

        metadata = {
            "signal_id": signal_id,
            "symbol": symbol,
            "direction": direction,
            "order_type": order_type,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit_1": take_profit_1,
            "take_profit_2": take_profit_2,
            "risk_reward_ratio": risk_reward_ratio,
            "confidence_score": confidence_score,
            "status": status,
            "outcome": outcome,
            "realized_pnl": realized_pnl,
            "channel_name": channel_name,
            "category": "signal",
            "created_at": created_at,
            "notes": notes or "",
        }

        vec, _ = await self.embedding_engine.get_embedding(text)
        doc = Document(
            id=f"sig-{signal_id}",
            text=text,
            doc_type="signal",
            title=f"{symbol} {direction} Signal",
            metadata=metadata,
            embedding=vec,
        )
        self.vector_store.add(doc)
        return doc

    async def query(
        self,
        query_text: str,
        top_k: int = 5,
        doc_type: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Interactive RAG Copilot query pipeline.
        1. Embed user query
        2. Retrieve hybrid top-k documents
        3. Formulate grounded prompt
        4. Generate synthesis
        """
        start_time = time.time()
        query_vec, embed_provider = await self.embedding_engine.get_embedding(query_text)
        embed_time_ms = round((time.time() - start_time) * 1000, 1)

        retrieval_start = time.time()
        results = self.vector_store.search(
            query=query_text,
            query_embedding=query_vec,
            top_k=top_k,
            doc_type=doc_type,
            symbol=symbol,
        )
        retrieval_time_ms = round((time.time() - retrieval_start) * 1000, 1)

        # Build context for LLM
        context_chunks: list[str] = []
        for i, res in enumerate(results, start=1):
            doc = res.document
            meta = doc.metadata
            chunk = (
                f"[Source {i} | Type: {doc.doc_type} | Title: {doc.title} | Match: {int(res.score * 100)}%]\n"
                f"{doc.text.strip()}"
            )
            context_chunks.append(chunk)

        context_str = "\n\n---\n\n".join(context_chunks) if context_chunks else "No specific documents found."

        prompt = (
            f"User Question: {query_text}\n\n"
            f"=== RETRIEVED GROUNDING CONTEXT ===\n"
            f"{context_str}\n\n"
            "=== INSTRUCTIONS ===\n"
            "Answer the user's trading inquiry using the retrieved context above. "
            "Highlight historical signal results, win rates, strategy alignments, and risk management rules. "
            "If citing historical trades or strategies, mention the relevant source numbers."
        )

        gen_start = time.time()
        answer, gen_provider = await self.llm_dispatcher.generate(prompt, results)
        gen_time_ms = round((time.time() - gen_start) * 1000, 1)

        # Format sources response
        sources = [
            {
                "id": r.document.id,
                "title": r.document.title,
                "doc_type": r.document.doc_type,
                "score": round(r.score, 3),
                "match_type": r.match_type,
                "snippet": r.document.text[:220] + "..." if len(r.document.text) > 220 else r.document.text,
                "metadata": r.document.metadata,
            }
            for r in results
        ]

        return {
            "query": query_text,
            "answer": answer,
            "sources": sources,
            "provider_used": f"{gen_provider} (embeddings: {embed_provider})",
            "metrics": {
                "retrieval_time_ms": retrieval_time_ms,
                "generation_time_ms": gen_time_ms,
                "total_time_ms": round((time.time() - start_time) * 1000, 1),
                "sources_retrieved": len(results),
            },
        }

    async def evaluate_signal(
        self,
        symbol: str,
        direction: str,
        order_type: str = "MARKET",
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit_1: Optional[float] = None,
        take_profit_2: Optional[float] = None,
        take_profit_3: Optional[float] = None,
        notes: Optional[str] = None,
        raw_text: Optional[str] = None,
    ) -> SignalEvaluationResult:
        """
        Performs in-depth RAG evaluation of a pending or incoming signal:
        - Retrieves top similar historical trades and their win/loss outcomes.
        - Retrieves relevant strategy rules (e.g. breakout volume, RSI divergence).
        - Computes historical setup win rate and risk score.
        - Delivers clear verdict: EXECUTE | CAUTION | REJECT.
        """
        # Formulate query for similar trades
        query_text = (
            f"{symbol} {direction} {order_type} "
            f"entry {entry_price or ''} sl {stop_loss or ''} "
            f"{notes or ''} {raw_text or ''}"
        )
        query_vec, _ = await self.embedding_engine.get_embedding(query_text)

        # Retrieve similar signals
        sig_results = self.vector_store.search(
            query=query_text,
            query_embedding=query_vec,
            top_k=6,
            doc_type="signal",
            symbol=symbol,
        )

        # Retrieve relevant strategies and risk rules
        strat_results = self.vector_store.search(
            query=f"{direction} trade setup {notes or ''} risk management",
            query_embedding=query_vec,
            top_k=3,
            doc_type=None,
        )

        # Extract similar trades
        similar_trades: list[SimilarTrade] = []
        wins = 0
        losses = 0

        for r in sig_results:
            meta = r.document.metadata
            sig_id = meta.get("signal_id", r.document.id)
            out = meta.get("outcome", "PENDING")
            pnl = meta.get("realized_pnl", 0.0)

            # Calculate pct return if entry exists
            ep = meta.get("entry_price")
            pnl_pct = None
            if ep and pnl:
                pnl_pct = (float(pnl) / float(ep)) * 100

            if out == "WIN":
                wins += 1
            elif out == "LOSS":
                losses += 1

            similar_trades.append(
                SimilarTrade(
                    signal_id=str(sig_id),
                    symbol=meta.get("symbol", symbol),
                    direction=meta.get("direction", direction),
                    entry_price=meta.get("entry_price"),
                    stop_loss=meta.get("stop_loss"),
                    take_profit=meta.get("take_profit_1"),
                    outcome=out,
                    realized_pnl=float(pnl) if pnl is not None else None,
                    realized_pnl_pct=round(pnl_pct, 2) if pnl_pct is not None else None,
                    similarity_score=round(r.score, 3),
                    channel_name=meta.get("channel_name", "Telegram Channel"),
                    created_at=meta.get("created_at", ""),
                    notes=meta.get("notes", ""),
                )
            )

        total_completed = wins + losses
        win_rate = (wins / total_completed * 100.0) if total_completed > 0 else 65.0

        # Calculate Risk/Reward ratio
        rr_ratio: Optional[float] = None
        if entry_price and stop_loss and take_profit_1:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit_1 - entry_price)
            if risk > 0:
                rr_ratio = reward / risk

        # Calculate Risk Score (0 = extremely safe, 100 = extreme risk)
        risk_score = 30  # Baseline moderate risk
        actionable_advice: list[str] = []

        if not stop_loss:
            risk_score += 40
            actionable_advice.append("⚠️ Missing stop loss: High liquidation risk. Mandatory SL required.")
        elif rr_ratio is not None and rr_ratio < 1.2:
            risk_score += 25
            actionable_advice.append(f"⚠️ Unfavorable R:R (1:{rr_ratio:.2f}): Below institutional minimum 1:1.5.")
        elif rr_ratio is not None and rr_ratio >= 2.0:
            risk_score -= 15
            actionable_advice.append(f"✅ Exceptional Risk-to-Reward ratio (1:{rr_ratio:.2f}).")

        if total_completed > 0:
            if win_rate < 40.0:
                risk_score += 20
                actionable_advice.append(f"⚠️ Low historical channel accuracy on similar {symbol} setups ({win_rate:.0f}% win rate).")
            elif win_rate >= 70.0:
                risk_score -= 10
                actionable_advice.append(f"✅ Strong historical precedent: Similar {symbol} trades had {win_rate:.0f}% win rate.")

        risk_score = max(5, min(95, risk_score))

        # Recommended Action Verdict
        if risk_score >= 70 or (stop_loss is None):
            verdict = "REJECT" if stop_loss is None else "CAUTION"
        elif risk_score <= 45 and (rr_ratio is None or rr_ratio >= 1.4):
            verdict = "EXECUTE"
        else:
            verdict = "CAUTION"

        # Matched strategies
        matched_strats = [r.document.title for r in strat_results if r.document.doc_type in ("strategy", "risk_rule")]

        # Detailed evaluation text
        eval_summary = (
            f"**RAG Verdict: {verdict}** (Risk Score: `{risk_score}/100` | Historical Win Rate: `{win_rate:.1f}%` across {total_completed} similar setups).\n"
            f"Analysis for **{symbol} {direction}**:\n"
            f"- Risk/Reward Ratio: {f'1:{rr_ratio:.2f}' if rr_ratio else 'Not specified'}\n"
            f"- Stop Loss Distance: {f'{abs(entry_price - stop_loss) / entry_price * 100:.2f}%' if (entry_price and stop_loss) else 'N/A'}\n"
            f"- Strategy Alignment: Grounded against '{matched_strats[0] if matched_strats else 'Standard Momentum'}'.\n"
        )
        if actionable_advice:
            eval_summary += "\n**Key Action Points:**\n" + "\n".join(f"- {a}" for a in actionable_advice)

        confidence = round(max(0.4, min(0.95, (win_rate / 100.0) * 0.7 + (1.0 - risk_score / 100.0) * 0.3)), 2)

        return SignalEvaluationResult(
            symbol=symbol,
            direction=direction,
            recommended_action=verdict,
            confidence_score=confidence,
            risk_score=risk_score,
            historical_win_rate_similar=round(win_rate, 1),
            sample_size_similar=total_completed,
            evaluation_summary=eval_summary,
            similar_trades=similar_trades,
            matched_strategies=matched_strats,
            actionable_advice=actionable_advice,
            provider_used=self.embedding_engine.provider,
        )

    async def reindex_all_from_db(self, db: AsyncSession) -> int:
        """Loads all existing Signals and Positions from the database and indexes them."""
        from app.models.signal import Signal
        from app.models.position import Position

        # Load all signals with their positions
        stmt = select(Signal).options(selectinload(Signal.positions))
        res = await db.execute(stmt)
        signals = res.scalars().all()

        indexed_count = 0
        for sig in signals:
            # Check if any associated position has realized PnL
            outcome = "PENDING"
            realized_pnl = 0.0
            if sig.positions:
                pos = sig.positions[0]
                if pos.status == "CLOSED":
                    pnl = float(pos.realized_pnl or 0.0)
                    realized_pnl = pnl
                    outcome = "WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "BREAKEVEN")
                elif pos.status == "OPEN":
                    outcome = "OPEN"
            elif sig.status == "EXECUTED":
                outcome = "EXECUTED"
            elif sig.status == "REJECTED":
                outcome = "REJECTED"

            await self.index_signal(
                signal_id=str(sig.id),
                symbol=sig.symbol,
                direction=sig.direction,
                order_type=sig.order_type,
                entry_price=float(sig.entry_price) if sig.entry_price else None,
                stop_loss=float(sig.stop_loss) if sig.stop_loss else None,
                take_profit_1=float(sig.take_profit_1) if sig.take_profit_1 else None,
                take_profit_2=float(sig.take_profit_2) if sig.take_profit_2 else None,
                confidence_score=float(sig.confidence_score) if sig.confidence_score else None,
                risk_reward_ratio=float(sig.risk_reward_ratio) if sig.risk_reward_ratio else None,
                notes=sig.notes,
                status=sig.status,
                outcome=outcome,
                realized_pnl=realized_pnl,
                channel_name="Telegram VIP Signals",
                created_at=sig.created_at.isoformat() if sig.created_at else None,
            )
            indexed_count += 1

        self.vector_store.save()
        logger.info("reindex_completed", signals_indexed=indexed_count)
        return indexed_count


# Global singleton instance
rag_service = RagService()
