"""
Curated Trading Knowledge Base
------------------------------
Collection of institutional-grade crypto trading playbooks, risk management frameworks,
and signal validation rules used as grounding context for RAG retrieval.
"""
from __future__ import annotations

from app.services.rag.models import Document

DEFAULT_KNOWLEDGE_DOCUMENTS: list[Document] = [
    Document(
        id="kb-strat-breakout",
        doc_type="strategy",
        title="Breakout & Volume Confirmation Strategy Playbook",
        text="""
STRATEGY: Breakout & Momentum Confirmation
Core Principle: A breakout occurs when price moves decisively beyond a well-established support or resistance level with elevated trading volume.
Entry Rules:
1. Wait for candle close above key horizontal resistance or trendline on 1H or 4H timeframe.
2. Volume confirmation: The breakout bar must show volume at least 1.5x above the 20-period volume moving average.
3. Retest Entry: Aggressive traders enter on initial breakout; conservative traders wait for a retest of broken resistance flipped to support.
Risk Management:
- Stop Loss: Must be placed below the breakout candle low or just below the broken resistance level (typically 2-4% below entry).
- Take Profit Targets: TP1 at 1.5x risk, TP2 at 2.5x risk, TP3 at next major weekly liquidity pool.
Invalidation & Caution:
- False breakouts ("bull traps"): If price immediately closes back inside the prior range within 2 candles, exit immediately.
- Never enter a breakout if the RSI on 4H is already above 80 (exhaustion zone).
""",
        metadata={
            "category": "strategy",
            "tags": ["breakout", "momentum", "volume", "resistance", "retest"],
            "recommended_timeframe": "1H/4H",
            "min_rr": 1.5,
        },
    ),
    Document(
        id="kb-strat-divergence",
        doc_type="strategy",
        title="RSI & MACD Momentum Divergence Strategy Playbook",
        text="""
STRATEGY: RSI & MACD Momentum Divergence Framework
Core Principle: Divergence indicates an underlying mismatch between price action and momentum oscillator strength, frequently preceding high-probability market reversals.
Types of Divergence:
1. Regular Bullish Divergence: Price forms Lower Lows while RSI / MACD Histogram forms Higher Lows. Strong reversal buy signal, especially at support or 200 EMA.
2. Regular Bearish Divergence: Price forms Higher Highs while RSI forms Lower Highs. Strong short / sell signal near key resistance.
3. Hidden Bullish Divergence (Trend Continuation): Price forms Higher Lows while RSI forms Lower Lows. Confirms continuation of prevailing uptrend.
Execution Criteria:
- Entry: Enter on the first candle confirming reversal (e.g., bullish engulfing or pin bar rejection) following the divergence signature.
- Stop Loss: Placed 0.5-1% beyond the swing high or swing low of the pattern.
- Take Profit: TP1 at the nearest Fibonacci retracement (0.382 or 0.50), TP2 at the opposing swing point.
Filters:
- Strongest when visible on 4H and Daily timeframes. 5-minute divergences have high noise and lower reliability.
""",
        metadata={
            "category": "strategy",
            "tags": ["rsi", "macd", "divergence", "reversal", "oscillator"],
            "recommended_timeframe": "4H/1D",
            "min_rr": 2.0,
        },
    ),
    Document(
        id="kb-risk-rules",
        doc_type="risk_rule",
        title="Institutional Risk Management & Position Sizing Framework",
        text="""
RISK RULE: Capital Preservation and Strict Position Sizing
Core Mandate: Capital preservation precedes profit generation. Never let a single trade risk portfolio survival.
Key Rules:
1. 2% Maximum Risk Rule: Risk no more than 1.0% to 2.0% of total portfolio equity on any single trade setup.
   Formula: Position Notional Size = (Total Equity * Risk Fraction) / (Abs(Entry Price - Stop Loss Price) / Entry Price)
2. Risk-to-Reward (R:R) Threshold: Minimum acceptable R:R is 1:1.5. Trades offering less than 1:1.2 expected return to risk must be rejected.
3. Drawdown Braking:
   - Daily loss limit: If cumulative losses reach 5.0% in 24 hours, halt all new trade entries.
   - Max portfolio drawdown: 20.0% hard circuit breaker. Reduce all position sizes by 50% if portfolio draws down > 10%.
4. Stop Loss Inviolability: Every trade MUST have a predetermined stop loss at order submission. Never widen a stop loss during an active drawdown.
5. Profit Realization & Breakeven:
   - When TP1 is hit (typically 50% of position closed), move stop loss to entry price (breakeven) to lock in a risk-free trade.
   - Trail stop loss using trailing stops or previous swing lows for remaining runner portions.
""",
        metadata={
            "category": "risk_rule",
            "tags": ["risk_management", "position_sizing", "drawdown", "stop_loss", "breakeven"],
            "max_risk_pct": 2.0,
            "min_rr": 1.5,
        },
    ),
    Document(
        id="kb-telegram-validation",
        doc_type="strategy",
        title="Telegram Trading Signal Quality & Manipulation Filter",
        text="""
VALIDATION PLAYBOOK: Telegram Crypto Signal Quality Control
Context: Public and VIP Telegram signal channels vary widely in quality and often suffer from delayed posting, unrealistic slippage, or pump-and-dump mechanics.
Validation Checklist:
1. Price Verification: Compare signal entry price with real-time Binance spot/futures market price. If current price has already moved more than 1.5% past entry towards TP1, reject the trade as chasing.
2. Stop Loss Reasonableness: Signals without a defined stop loss or with an excessively wide stop loss (> 12% on high leverage) indicate low-skill channel providers.
3. Multi-Target Distribution: Look for structured take-profit distribution:
   - TP1 (conservative): 35-50% position scale out.
   - TP2 (target): 30-35% position scale out.
   - TP3 (moonbag): 15-20% trailing runner.
4. Channel Historical Reliability: Channels with persistent negative expectancy or rapid SL triggers should have their position sizing automatically curtailed to 0.5% equity.
5. Overtrading Filter: Reject simultaneous opposite signals on the same crypto asset within 30 minutes.
""",
        metadata={
            "category": "signal_validation",
            "tags": ["telegram", "validation", "slippage", "channel_quality", "take_profit"],
            "slippage_tolerance_pct": 1.5,
        },
    ),
    Document(
        id="kb-strat-support-resistance",
        doc_type="strategy",
        title="Support, Resistance, and Liquidity Sweeps Strategy",
        text="""
STRATEGY: Key Levels, Order Blocks, and Liquidity Sweeps
Core Principle: Crypto markets seek liquidity resting above equal highs and below equal lows before making substantial directional moves.
Trading Rules:
1. Liquidity Sweeps (Stop Hunts): When price quickly wicks below an obvious support level to trigger retail stop losses and immediately recovers with high volume, enter LONG with tight stop loss below the wick low.
2. Order Blocks: Identify the last down-candle before a violent upward expansion (Bullish Order Block). Place limit orders in the upper 50% equilibrium zone of that block on retest.
3. S/R Flip Confirmation: Former resistance becomes future support. A clean retest with decreasing sell volume confirms institutional absorption.
4. Profit Targets: Aim for opposing liquidity pools (e.g. untapped highs or resting sell stops).
""",
        metadata={
            "category": "strategy",
            "tags": ["support", "resistance", "liquidity_sweep", "order_block", "smart_money"],
            "recommended_timeframe": "15m/1H/4H",
            "min_rr": 2.5,
        },
    ),
    Document(
        id="kb-market-volatility",
        doc_type="risk_rule",
        title="Macro Volatility, BTC Dominance & News Event Safeguards",
        text="""
RISK RULE: Macro Event Volatility & BTC Dominance Alignment
Core Principle: Altcoin trading signals are heavily subordinated to Bitcoin macro trend and Federal Reserve macroeconomic volatility events.
Safeguards:
1. BTC Dominance (BTC.D) Impact:
   - When BTC.D is rising sharply alongside BTC price: Altcoins bleed. Avoid aggressive altcoin longs; prioritize BTC or selective shorts.
   - When BTC is consolidating at highs and BTC.D drops: Prime "Altseason" condition for aggressive altcoin breakout longs.
2. High-Impact News Events: During US CPI, PPI, FOMC rate decisions, or major exchange regulatory actions:
   - Widen spreads and severe slippage occur.
   - Pause automated execution 15 minutes before and 30 minutes after major macroeconomic releases.
3. Funding Rate Warning: Extreme positive funding (> +0.05% per 8h) signals crowded longs vulnerable to long squeeze flushes.
""",
        metadata={
            "category": "macro",
            "tags": ["bitcoin", "btc_dominance", "macro", "fomc", "funding_rates", "volatility"],
        },
    ),
]
