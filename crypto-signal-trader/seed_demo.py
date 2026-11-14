"""
Seed the running CryptoSignal AI backend with realistic demo data.
Run while backend is live: python seed_demo.py
"""
import urllib.request
import json
import time

BASE = "http://127.0.0.1:8000"

SIGNALS = [
    {
        "symbol": "ETH/USDT",
        "direction": "BUY",
        "order_type": "LIMIT",
        "entry_price": 2650.0,
        "stop_loss": 2540.0,
        "take_profit_1": 2780.0,
        "take_profit_2": 2920.0,
        "notes": "ETH breaking above key resistance at 2650. Strong volume confirmation.\n\nEntry: 2650 | SL: 2540 | TP1: 2780 | TP2: 2920",
    },
    {
        "symbol": "SOL/USDT",
        "direction": "BUY",
        "order_type": "MARKET",
        "entry_price": 172.5,
        "stop_loss": 163.0,
        "take_profit_1": 185.0,
        "take_profit_2": 198.0,
        "take_profit_3": 215.0,
        "notes": "SOL/USDT LONG\nEntry Zone: 170-175 | SL: 163 | TP1: 185 | TP2: 198 | TP3: 215",
    },
    {
        "symbol": "BNB/USDT",
        "direction": "SELL",
        "order_type": "LIMIT",
        "entry_price": 595.0,
        "stop_loss": 615.0,
        "take_profit_1": 565.0,
        "take_profit_2": 540.0,
        "notes": "BNB SHORT - Rejection at 600 resistance\nEntry: 595 | SL: 615 | TP1: 565 | TP2: 540\nRSI overbought on 4H. MACD bearish crossover.",
    },
    {
        "symbol": "ADA/USDT",
        "direction": "BUY",
        "order_type": "MARKET",
        "entry_price": 0.445,
        "stop_loss": 0.415,
        "take_profit_1": 0.485,
        "take_profit_2": 0.520,
        "notes": "ADA breakout confirmed\nPrice breaking out of 3-week consolidation.\nEntry: 0.445 | SL: 0.415 | TP1: 0.485 | TP2: 0.520",
    },
    {
        "symbol": "BTC/USDT",
        "direction": "SELL",
        "order_type": "LIMIT",
        "entry_price": 69500.0,
        "stop_loss": 71200.0,
        "take_profit_1": 66000.0,
        "take_profit_2": 63500.0,
        "notes": "BTC SHORT scalp\nDouble top at 70k. Rejection signal.\nEntry: 69500 | SL: 71200 | TP1: 66000 | TP2: 63500",
    },
    {
        "symbol": "MATIC/USDT",
        "direction": "BUY",
        "order_type": "LIMIT",
        "entry_price": 0.52,
        "stop_loss": 0.475,
        "take_profit_1": 0.58,
        "take_profit_2": 0.64,
        "notes": "MATIC/USDT LONG\nKey support bounce at 0.52\nEntry: 0.52 | SL: 0.475 | TP1: 0.58 | TP2: 0.64",
    },
    {
        "symbol": "LINK/USDT",
        "direction": "BUY",
        "order_type": "MARKET",
        "entry_price": 13.85,
        "stop_loss": 12.90,
        "take_profit_1": 15.20,
        "take_profit_2": 16.80,
        "notes": "LINK breaking out of falling wedge pattern.\nBullish divergence on RSI daily chart.\nEntry: 13.85 | SL: 12.90 | TP1: 15.20 | TP2: 16.80",
    },
    {
        "symbol": "AVAX/USDT",
        "direction": "SELL",
        "order_type": "MARKET",
        "entry_price": 36.40,
        "stop_loss": 38.50,
        "take_profit_1": 33.20,
        "take_profit_2": 30.80,
        "notes": "AVAX breakdown confirmed\nFailed to hold 37 support.\nEntry: 36.40 | SL: 38.50 | TP1: 33.20 | TP2: 30.80",
    },
]

def post(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def get(url):
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read().decode())

print("=" * 55)
print("  CryptoSignal AI - Demo Data Seeder")
print("=" * 55)

health = get(f"{BASE}/health")
print(f"\n Backend: {health['status']} | Market Data: {health['market_data_connected']}")

print(f"\n Seeding {len(SIGNALS)} signals...\n")
for sig in SIGNALS:
    try:
        result = post(f"{BASE}/api/v1/signals", sig)
        arrow = "BUY ^" if result["direction"] == "BUY" else "SELL v"
        print(f"  {result['symbol']:12s}  {arrow:6s}  status={result['status']}")
        time.sleep(0.3)
    except Exception as e:
        print(f"  Failed: {sig['symbol']} - {e}")

print("\n Dashboard Summary:")
dash = get(f"{BASE}/api/v1/dashboard")
p = dash["portfolio"]
print(f"  Portfolio Equity : ${p['total_equity']:,.2f}")
print(f"  Cash Available   : ${p['cash_balance']:,.2f}")
print(f"  Open Positions   : {dash['open_positions_count']}")
print(f"  Total Signals    : {len(dash['recent_signals'])}")
print(f"  Total Orders     : {len(dash['recent_orders'])}")

print("\n Done! Open http://localhost:5173 to see the UI.\n")
