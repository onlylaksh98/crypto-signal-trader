"""
CryptoSignal AI — Telegram Trading Terminal
Core configuration using Pydantic Settings v2.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "CryptoSignal AI"
    app_env: str = "development"
    app_secret_key: str = Field(
        default="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
        min_length=32,
    )
    log_level: str = "INFO"
    base_dir: Path = Path(__file__).resolve().parent.parent.parent

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./crypto_signal_trader.db"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Telegram ──────────────────────────────────────────────────────────────
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_session_string: str = ""
    telegram_session_dir: Path = Path("/app/sessions")

    # ── Market Data ───────────────────────────────────────────────────────────
    market_data_exchange: str = "binance"
    market_data_timeout_ms: int = 10_000

    # ── Paper Trading (non-negotiable: always enabled) ────────────────────────
    paper_trading_enabled: bool = True
    paper_initial_balance_usdt: float = 10_000.0
    paper_default_position_size_pct: float = 2.0
    paper_max_open_positions: int = 10
    paper_slippage_bps: int = 5

    # ── Risk Engine ────────────────────────────────────────────────────────────
    risk_max_drawdown_pct: float = 20.0
    risk_max_daily_loss_pct: float = 5.0
    risk_max_position_size_pct: float = 10.0

    # ── CORS ───────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Binance Testnet (optional) ─────────────────────────────────────────────
    binance_testnet_api_key: str = ""
    binance_testnet_secret: str = ""

    # ── Retrieval-Augmented Generation (RAG) & AI Copilot ──────────────────────
    gemini_api_key: str = ""
    openai_api_key: str = ""
    rag_provider: str = "auto"              # auto | gemini | openai | local
    rag_embedding_model: str = "text-embedding-004"
    rag_llm_model: str = "gemini-1.5-flash"
    rag_top_k: int = 5
    rag_min_similarity: float = 0.25
    rag_auto_enrich_signals: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @model_validator(mode="after")
    def enforce_paper_trading(self) -> "Settings":
        if not self.paper_trading_enabled:
            raise ValueError(
                "PAPER_TRADING_ENABLED must be true. "
                "Live trading is not supported in this version."
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_api_id and self.telegram_api_hash)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
