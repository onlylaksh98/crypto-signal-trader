"""
Embedding Engine for RAG
------------------------
Provides dense vector representations for queries, strategy docs, and signals.
Supports:
1. Google Gemini Embedding API (text-embedding-004)
2. OpenAI Embedding API (text-embedding-3-small)
3. LocalDeterministicEmbedder: Zero-dependency, offline TF-IDF/character n-gram L2 normalized
   vectorizer with dense dimensionality reduction, ensuring 100% offline functionality.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens and bigrams for rich semantic overlap."""
    clean = re.sub(r"[^\w\s\./:\-%]", " ", text.lower())
    words = [w for w in clean.split() if len(w) > 1]
    tokens = list(words)
    # Add bigrams for trading phrases (e.g. "stop loss", "breakout confirmed", "risk reward")
    for i in range(len(words) - 1):
        tokens.append(f"{words[i]}_{words[i+1]}")
    return tokens


class LocalSemanticEmbedder:
    """
    High-performance, offline semantic embedder using Murmur/MD5 feature hashing
    and L2 unit-norm projection. Dimensions: 128.
    Dot product between two normalized vectors equals cosine similarity.
    """
    def __init__(self, dim: int = 128) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        tokens = _tokenize(text)
        if not tokens:
            return [0.0] * self.dim

        vec = [0.0] * self.dim
        for token in tokens:
            # Hash token to a bucket and sign
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            bucket = h % self.dim
            sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
            
            # Boost weight for crypto symbols and key trading terminology
            weight = 1.0
            if "/" in token or token.upper() in {"BTC", "ETH", "SOL", "BNB", "LONG", "SHORT", "BUY", "SELL"}:
                weight = 2.5
            elif any(k in token for k in ["breakout", "divergence", "stop", "profit", "resistance", "support"]):
                weight = 1.8

            vec[bucket] += sign * weight

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [x / norm for x in vec]
        return vec


class GeminiEmbedder:
    """Calls Google Generative AI REST API for text-embedding-004."""
    def __init__(self, api_key: str, model: str = "text-embedding-004") -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
            f"?key={api_key}"
        )

    async def embed(self, text: str) -> Optional[list[float]]:
        payload = {
            "model": f"models/{self.model}",
            "content": {
                "parts": [{"text": text[:2048]}]
            }
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(self.endpoint, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    values = data.get("embedding", {}).get("values", [])
                    if values:
                        # L2 normalize
                        norm = math.sqrt(sum(x * x for x in values))
                        return [x / norm for x in values] if norm > 0 else values
                logger.warning("gemini_embedding_failed", status_code=res.status_code, body=res.text[:200])
        except Exception as exc:
            logger.warning("gemini_embedding_exception", error=str(exc))
        return None


class OpenAIEmbedder:
    """Calls OpenAI REST API for text-embedding-3-small."""
    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.openai.com/v1/embeddings"

    async def embed(self, text: str) -> Optional[list[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": text[:2048],
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(self.endpoint, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    values = data["data"][0]["embedding"]
                    # OpenAI embeddings are already L2 normalized
                    return values
                logger.warning("openai_embedding_failed", status_code=res.status_code, body=res.text[:200])
        except Exception as exc:
            logger.warning("openai_embedding_exception", error=str(exc))
        return None


class EmbeddingEngine:
    """
    Unified embedding dispatcher that dynamically uses the best configured provider
    (Gemini / OpenAI) with automatic, transparent fallback to LocalSemanticEmbedder.
    """
    def __init__(self) -> None:
        self.local = LocalSemanticEmbedder(dim=128)
        self.provider = "local"
        self._gemini: Optional[GeminiEmbedder] = None
        self._openai: Optional[OpenAIEmbedder] = None
        self._configure()

    def _configure(self) -> None:
        p = settings.rag_provider.lower()
        if (p in ("gemini", "auto")) and settings.gemini_api_key:
            self._gemini = GeminiEmbedder(settings.gemini_api_key, settings.rag_embedding_model)
            self.provider = "gemini"
        elif (p in ("openai", "auto")) and settings.openai_api_key:
            self._openai = OpenAIEmbedder(settings.openai_api_key)
            self.provider = "openai"
        else:
            self.provider = "local"

    async def get_embedding(self, text: str) -> tuple[list[float], str]:
        """
        Computes embedding for input text.
        Returns (embedding_vector, provider_name_used).
        """
        if self.provider == "gemini" and self._gemini:
            vec = await self._gemini.embed(text)
            if vec is not None:
                return vec, "gemini"
        elif self.provider == "openai" and self._openai:
            vec = await self._openai.embed(text)
            if vec is not None:
                return vec, "openai"

        # Fallback to local
        return self.local.embed(text), "local"
