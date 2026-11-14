import urllib.request
import json

def test_api():
    print("Testing GET /health...")
    with urllib.request.urlopen("http://127.0.0.1:8000/health") as resp:
        print("Health:", resp.read().decode())

    print("\nCreating manual paper trade signal...")
    payload = {
        "symbol": "BTC/USDT",
        "direction": "BUY",
        "order_type": "MARKET",
        "entry_price": 68000,
        "stop_loss": 65000,
        "take_profit_1": 72000,
        "notes": "Automated verification signal"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/signals",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        print("Signal created:", resp.read().decode())

    print("\nFetching updated dashboard...")
    with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/dashboard") as resp:
        dash = json.loads(resp.read().decode())
        print(f"Portfolio equity: {dash['portfolio']['total_equity']}")
        print(f"Open positions count: {dash['open_positions_count']}")
        print(f"Recent signals: {len(dash['recent_signals'])}")
        print(f"Recent orders: {len(dash['recent_orders'])}")

if __name__ == "__main__":
    test_api()
