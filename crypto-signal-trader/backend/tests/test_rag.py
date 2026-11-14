"""
Unit and integration tests for RAG (Retrieval-Augmented Generation) subsystem.
"""
import pytest
from app.services.rag.embeddings import LocalSemanticEmbedder
from app.services.rag.models import Document
from app.services.rag.vector_store import HybridVectorStore
from app.services.rag.rag_service import RagService


def test_local_semantic_embedder():
    embedder = LocalSemanticEmbedder(dim=128)
    vec1 = embedder.embed("BTC/USDT breakout buy signal at resistance")
    vec2 = embedder.embed("BTC long breakout confirmed with volume")
    vec3 = embedder.embed("weather forecast sunny recipe for soup")

    assert len(vec1) == 128
    assert len(vec2) == 128
    assert len(vec3) == 128

    # Check L2 unit norm
    norm1 = sum(x * x for x in vec1) ** 0.5
    assert abs(norm1 - 1.0) < 1e-4

    # Dot product between similar crypto queries should exceed dot product with irrelevant query
    dot_similar = sum(a * b for a, b in zip(vec1, vec2))
    dot_unrelated = sum(a * b for a, b in zip(vec1, vec3))
    assert dot_similar > dot_unrelated


def test_hybrid_vector_store(tmp_path):
    store = HybridVectorStore(persistence_path=str(tmp_path / "test_store.json"))
    embedder = LocalSemanticEmbedder(dim=128)

    doc1 = Document(
        id="doc-1",
        title="Breakout Strategy",
        doc_type="strategy",
        text="Breakout strategy requires 1.5x volume above average and confirmation above resistance.",
        metadata={"symbol": "BTC/USDT"},
        embedding=embedder.embed("Breakout strategy requires 1.5x volume above average"),
    )
    doc2 = Document(
        id="doc-2",
        title="RSI Divergence Strategy",
        doc_type="strategy",
        text="RSI divergence signals reversal on 4H chart when price makes lower lows and RSI higher lows.",
        metadata={"symbol": "ETH/USDT"},
        embedding=embedder.embed("RSI divergence signals reversal on 4H chart"),
    )

    store.add(doc1)
    store.add(doc2)

    # Search for breakout
    q_vec = embedder.embed("How to trade volume breakout?")
    results = store.search("How to trade volume breakout?", query_embedding=q_vec, top_k=2)

    assert len(results) >= 1
    assert any(r.document.id == "doc-1" for r in results)


@pytest.mark.asyncio
async def test_rag_service_initialization_and_query():
    service = RagService()
    await service.initialize()

    assert len(service.vector_store.documents) >= 6

    # Test interactive query
    res = await service.query("What is the maximum risk per trade in our risk rules?")
    assert "answer" in res
    assert len(res["sources"]) > 0
    assert "provider_used" in res


@pytest.mark.asyncio
async def test_rag_signal_evaluation():
    service = RagService()
    await service.initialize()

    # Index sample historical signal
    await service.index_signal(
        signal_id="sig-test-1",
        symbol="SOL/USDT",
        direction="BUY",
        order_type="MARKET",
        entry_price=172.5,
        stop_loss=163.0,
        take_profit_1=185.0,
        take_profit_2=198.0,
        notes="SOL breakout above key resistance",
        status="EXECUTED",
        outcome="WIN",
        realized_pnl=240.0,
        channel_name="VIP Crypto Signals",
    )

    # Evaluate new pending signal
    eval_result = await service.evaluate_signal(
        symbol="SOL/USDT",
        direction="BUY",
        order_type="MARKET",
        entry_price=173.0,
        stop_loss=164.0,
        take_profit_1=186.0,
        notes="SOL long breakout continuation",
    )

    assert eval_result.symbol == "SOL/USDT"
    assert eval_result.direction == "BUY"
    assert eval_result.recommended_action in ("EXECUTE", "CAUTION", "REJECT")
    assert eval_result.risk_score >= 0 and eval_result.risk_score <= 100
    assert len(eval_result.similar_trades) > 0
    assert eval_result.similar_trades[0].outcome == "WIN"
