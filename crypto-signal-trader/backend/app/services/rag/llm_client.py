"""
LLM Generation Client for RAG
-----------------------------
Supports:
1. Google Gemini (e.g. gemini-1.5-flash, gemini-2.0-flash)
2. OpenAI (e.g. gpt-4o-mini, gpt-4o)
3. Deterministic Heuristic Synthesizer (offline, zero external API keys required)
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.rag.models import SearchResult, SimilarTrade

logger = get_logger(__name__)


SYSTEM_PROMPT = """You are CryptoSignal AI Copilot, an elite quantitative crypto trading assistant and risk officer.
You analyze trading signals, historical performance, risk parameters, and strategy playbooks using Retrieval-Augmented Generation (RAG).

Always base your answers strictly on the retrieved context provided.
When analyzing a trade or signal:
1. Reference historical similar trade setups and their outcomes (win rate, realized P&L).
2. Evaluate risk-to-reward ratio against the 1.5 minimum threshold.
3. Apply the 1-2% max equity risk rule.
4. State whether the signal aligns with strategy rules (e.g. breakout volume, RSI divergence).
5. Deliver concise, clear, and actionable conclusions formatted in clean Markdown with bullet points.
Be objective, realistic, and risk-averse. Never recommend reckless leverage or unvalidated chasing."""


class GeminiLLMClient:
    """Invokes Google Gemini API via REST."""
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            f"?key={api_key}"
        )

    async def generate(self, prompt: str, system_instruction: str = SYSTEM_PROMPT) -> Optional[str]:
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            }
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(self.endpoint, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                logger.warning("gemini_generation_failed", status_code=res.status_code, body=res.text[:200])
        except Exception as exc:
            logger.warning("gemini_generation_exception", error=str(exc))
        return None


class OpenAILLMClient:
    """Invokes OpenAI API via REST."""
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    async def generate(self, prompt: str, system_instruction: str = SYSTEM_PROMPT) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(self.endpoint, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"].strip()
                logger.warning("openai_generation_failed", status_code=res.status_code, body=res.text[:200])
        except Exception as exc:
            logger.warning("openai_generation_exception", error=str(exc))
        return None


class DeterministicHeuristicSynthesizer:
    """
    Offline analytical generator that synthesizes retrieved context,
    historical statistics, and strategy documents into a structured, high-value report.
    """

    def synthesize_query(self, query: str, results: list[SearchResult]) -> str:
        if not results:
            return (
                "### ℹ️ No Direct Knowledge Base Matches Found\n\n"
                f"I searched the vector database for **'{query}'**, but did not find high-confidence "
                "historical trade signals or strategy documents matching this specific inquiry.\n\n"
                "**Suggestions:**\n"
                "- Try querying specific asset symbols like `ETH/USDT` or `SOL/USDT`.\n"
                "- Query trading strategies such as *'breakout volume confirmation'*, *'RSI divergence'*, or *'risk rules'*.\n"
                "- Index more historical signals from Telegram channels."
            )

        # Categorize results
        signals = [r for r in results if r.document.doc_type == "signal"]
        strategies = [r for r in results if r.document.doc_type in ("strategy", "risk_rule")]

        lines = [f"### 🤖 AI Copilot Analysis: *{query}*\n"]

        # If there are historical trades
        if signals:
            lines.append("#### 📊 Historical Trade Retrieval & Outcomes")
            wins = 0
            losses = 0
            pnl_sum = 0.0

            for r in signals[:4]:
                doc = r.document
                meta = doc.metadata
                outcome = meta.get("outcome", "PENDING")
                pnl = meta.get("realized_pnl", 0.0)
                sym = meta.get("symbol", doc.title)
                dir_ = meta.get("direction", "")
                pnl_sum += float(pnl or 0.0)
                if outcome == "WIN":
                    wins += 1
                elif outcome == "LOSS":
                    losses += 1

                badge = "🟢 WIN" if outcome == "WIN" else ("🔴 LOSS" if outcome == "LOSS" else "🟡 " + outcome)
                lines.append(
                    f"- **{sym} {dir_}** [{badge}] (Match: {int(r.score * 100)}%): "
                    f"Entry {meta.get('entry_price', 'Market')} | SL {meta.get('stop_loss', 'N/A')} | P&L: ${float(pnl or 0):+.2f}"
                )

            total_trades = wins + losses
            if total_trades > 0:
                win_rate = (wins / total_trades) * 100
                lines.append(
                    f"\n**Retrieved Setups Win Rate:** `{win_rate:.1f}%` ({wins} Wins / {losses} Losses) "
                    f"| Cumulative Realized P&L: `${pnl_sum:+.2f}`"
                )
            lines.append("")

        # If there are strategies/rules
        if strategies:
            lines.append("#### 📘 Relevant Strategy Playbooks & Risk Guidelines")
            for r in strategies[:3]:
                doc = r.document
                lines.append(f"**{doc.title}** *(Relevance: {int(r.score * 100)}%)*:")
                # Extract first 2-3 substantive lines of doc
                summary_lines = [
                    line.strip() for line in doc.text.strip().split("\n")
                    if line.strip() and not line.startswith("STRATEGY:") and not line.startswith("RISK RULE:")
                ][:3]
                for sl in summary_lines:
                    lines.append(f"> {sl}")
                lines.append("")

        # Actionable recommendation
        lines.append("#### 🎯 Execution Takeaways")
        lines.append("- Verify risk is within 1.0% - 2.0% of portfolio equity before submitting simulated orders.")
        lines.append("- Move stop-loss to breakeven once Take Profit 1 is triggered.")
        lines.append("- Reference live Binance bid/ask price to ensure slippage does not exceed 10 basis points.")

        return "\n".join(lines)


class LLMDispatcher:
    """Unified dispatcher for generation with automatic fallback."""
    def __init__(self) -> None:
        self.heuristic = DeterministicHeuristicSynthesizer()
        self._gemini: Optional[GeminiLLMClient] = None
        self._openai: Optional[OpenAILLMClient] = None
        self._configure()

    def _configure(self) -> None:
        p = settings.rag_provider.lower()
        if (p in ("gemini", "auto")) and settings.gemini_api_key:
            self._gemini = GeminiLLMClient(settings.gemini_api_key, settings.rag_llm_model)
        if (p in ("openai", "auto")) and settings.openai_api_key:
            self._openai = OpenAILLMClient(settings.openai_api_key)

    async def generate(self, prompt: str, context_results: list[SearchResult], system_instruction: str = SYSTEM_PROMPT) -> tuple[str, str]:
        """
        Attempts to generate response via Gemini or OpenAI,
        falling back to DeterministicHeuristicSynthesizer.
        Returns (text, provider_name).
        """
        # Try Gemini
        if self._gemini:
            ans = await self._gemini.generate(prompt, system_instruction)
            if ans:
                return ans, "gemini"

        # Try OpenAI
        if self._openai:
            ans = await self._openai.generate(prompt, system_instruction)
            if ans:
                return ans, "openai"

        # Fallback to local deterministic synthesis
        return self.heuristic.synthesize_query(prompt, context_results), "local"
