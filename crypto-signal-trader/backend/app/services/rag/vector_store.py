"""
Vector and Hybrid Document Store
--------------------------------
In-memory vector store with persistence to JSON.
Features:
- Dense cosine similarity matching
- Sparse token-overlap keyword scoring
- Reciprocal rank fusion and exact symbol boost
- Metadata filtering (by symbol, doc_type, direction)
"""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.rag.models import Document, SearchResult

logger = get_logger(__name__)


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec1 or not vec2:
        return 0.0
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    length = min(len(vec1), len(vec2))
    for i in range(length):
        dot += vec1[i] * vec2[i]
        norm1 += vec1[i] * vec1[i]
        norm2 += vec2[i] * vec2[i]

    if norm1 <= 0.0 or norm2 <= 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (math.sqrt(norm1) * math.sqrt(norm2))))


def _keyword_overlap(query_tokens: set[str], doc_tokens: set[str]) -> float:
    """Calculates Jaccard / token-overlap score between query and document text."""
    if not query_tokens or not doc_tokens:
        return 0.0
    intersection = query_tokens.intersection(doc_tokens)
    return len(intersection) / math.sqrt(len(query_tokens) * len(doc_tokens))


class HybridVectorStore:
    """In-memory hybrid vector & document store with persistent disk caching."""

    def __init__(self, persistence_path: Optional[str] = None) -> None:
        self.documents: dict[str, Document] = {}
        if persistence_path:
            self.persistence_path = Path(persistence_path)
        else:
            self.persistence_path = Path(settings.base_dir) / "rag_index.json"
        self._load()

    def add(self, doc: Document) -> None:
        """Add or update a document in the store."""
        self.documents[doc.id] = doc

    def add_many(self, docs: list[Document]) -> None:
        for doc in docs:
            self.documents[doc.id] = doc

    def get(self, doc_id: str) -> Optional[Document]:
        return self.documents.get(doc_id)

    def delete(self, doc_id: str) -> bool:
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False

    def list_all(self, doc_type: Optional[str] = None) -> list[Document]:
        if not doc_type:
            return list(self.documents.values())
        return [d for d in self.documents.values() if d.doc_type == doc_type]

    def search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 5,
        doc_type: Optional[str] = None,
        symbol: Optional[str] = None,
        min_score: float = 0.15,
    ) -> list[SearchResult]:
        """
        Hybrid retrieval combining semantic dense embedding similarity
        with token keyword overlap and exact symbol match boosting.
        """
        clean_q = re.sub(r"[^\w\s\./:\-%]", " ", query.lower())
        q_tokens = set(clean_q.split())
        q_symbol = symbol.upper() if symbol else None
        
        # Check if query contains any symbol like "BTC" or "ETH/USDT"
        if not q_symbol:
            for word in q_tokens:
                clean_sym = word.upper()
                if "USDT" in clean_sym or clean_sym in {"BTC", "ETH", "SOL", "BNB", "ADA", "XRP", "MATIC", "LINK", "AVAX"}:
                    q_symbol = clean_sym.replace("/USDT", "").replace("USDT", "") + "/USDT"
                    break

        candidates: list[SearchResult] = []

        for doc in self.documents.values():
            if doc_type and doc.doc_type != doc_type:
                continue

            # Compute semantic vector score
            v_score = 0.0
            if query_embedding and doc.embedding:
                v_score = _cosine_similarity(query_embedding, doc.embedding)

            # Compute keyword score
            d_clean = re.sub(r"[^\w\s\./:\-%]", " ", doc.text.lower())
            d_tokens = set(d_clean.split())
            k_score = _keyword_overlap(q_tokens, d_tokens)

            # Combined hybrid score (65% vector + 35% keyword)
            combined = 0.65 * v_score + 0.35 * k_score

            # Exact symbol bonus boost if matching
            doc_sym = doc.metadata.get("symbol")
            if q_symbol and doc_sym:
                if q_symbol.split("/")[0] in doc_sym:
                    combined += 0.25

            # Doc title match boost
            if doc.title and any(t in doc.title.lower() for t in q_tokens):
                combined += 0.10

            final_score = min(1.0, max(0.0, combined))
            if final_score >= min_score or (v_score > 0.40):
                match_type = "hybrid"
                if v_score > 0.65 and k_score < 0.2:
                    match_type = "semantic"
                elif k_score > 0.5 and v_score < 0.3:
                    match_type = "keyword"

                candidates.append(
                    SearchResult(
                        document=doc,
                        score=final_score,
                        match_type=match_type,
                        keyword_score=round(k_score, 4),
                        vector_score=round(v_score, 4),
                    )
                )

        # Sort descending by score
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:top_k]

    def count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for d in self.documents.values():
            counts[d.doc_type] = counts.get(d.doc_type, 0) + 1
        return counts

    def save(self) -> None:
        """Persist documents and embeddings to disk."""
        try:
            data = [doc.to_dict() for doc in self.documents.values()]
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info("rag_vector_store_saved", count=len(data), path=str(self.persistence_path))
        except Exception as exc:
            logger.error("rag_vector_store_save_error", error=str(exc))

    def _load(self) -> None:
        """Load persisted index from disk if available."""
        if not self.persistence_path.exists():
            return
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                doc = Document.from_dict(item)
                self.documents[doc.id] = doc
            logger.info("rag_vector_store_loaded", count=len(self.documents))
        except Exception as exc:
            logger.warning("rag_vector_store_load_warning", error=str(exc))
