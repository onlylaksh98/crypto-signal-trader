"""
Market Hours Service
--------------------
Calculates real-time trading session status, opening & closing times,
timezones, countdowns, and active market sessions for major global stock exchanges
(NYSE/NASDAQ, NSE/BSE, LSE, TSE, HKEX, XETRA) and 24/7 Crypto markets.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any, Dict, List


EXCHANGES_CONFIG = [
    {
        "id": "nyse",
        "name": "New York Stock Exchange",
        "short_name": "NYSE / NASDAQ",
        "region": "United States",
        "flag": "🇺🇸",
        "timezone": "America/New_York",
        "tz_label": "EST/EDT",
        "open_time": time(9, 30),
        "close_time": time(16, 0),
        "has_pre_market": True,
        "pre_market_open": time(4, 0),
        "has_after_hours": True,
        "after_hours_close": time(20, 0),
        "crypto_impact": "High — Drives Bitcoin ETF volumes, macro liquidity & institutional flows.",
    },
    {
        "id": "nse",
        "name": "National Stock Exchange of India",
        "short_name": "NSE / BSE",
        "region": "India",
        "flag": "🇮🇳",
        "timezone": "Asia/Kolkata",
        "tz_label": "IST",
        "open_time": time(9, 15),
        "close_time": time(15, 30),
        "has_pre_market": True,
        "pre_market_open": time(9, 0),
        "has_after_hours": False,
        "crypto_impact": "Moderate — High retail adoption, active emerging market sentiment.",
    },
    {
        "id": "lse",
        "name": "London Stock Exchange",
        "short_name": "LSE",
        "region": "United Kingdom",
        "flag": "🇬🇧",
        "timezone": "Europe/London",
        "tz_label": "GMT/BST",
        "open_time": time(8, 0),
        "close_time": time(16, 30),
        "has_pre_market": False,
        "has_after_hours": False,
        "crypto_impact": "High — Major European FX overlap & institutional crypto trading window.",
    },
    {
        "id": "tse",
        "name": "Tokyo Stock Exchange",
        "short_name": "TSE",
        "region": "Japan",
        "flag": "🇯🇵",
        "timezone": "Asia/Tokyo",
        "tz_label": "JST",
        "open_time": time(9, 0),
        "close_time": time(15, 30),
        "has_pre_market": False,
        "has_after_hours": False,
        "crypto_impact": "Moderate — Key Asian market bellwether, Yen carry trade implications.",
    },
    {
        "id": "hkex",
        "name": "Hong Kong Exchanges",
        "short_name": "HKEX",
        "region": "Hong Kong",
        "flag": "🇭🇰",
        "timezone": "Asia/Hong_Kong",
        "tz_label": "HKT",
        "open_time": time(9, 30),
        "close_time": time(16, 0),
        "has_pre_market": False,
        "has_after_hours": False,
        "crypto_impact": "High — Asian spot crypto ETF liquidity, China-adjacent sentiment.",
    },
    {
        "id": "xetra",
        "name": "Frankfurt Stock Exchange",
        "short_name": "Deutsche Börse / XETRA",
        "region": "Germany / EU",
        "flag": "🇩🇪",
        "timezone": "Europe/Berlin",
        "tz_label": "CET/CEST",
        "open_time": time(9, 0),
        "close_time": time(17, 30),
        "has_pre_market": False,
        "has_after_hours": False,
        "crypto_impact": "Moderate — Eurozone financial liquidity, ETN trading activity.",
    },
]


def _format_timedelta(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m {seconds}s"


class MarketHoursService:
    """Computes real-time market sessions, active status, countdowns, and current dates."""

    @staticmethod
    def get_exchange_status(config: Dict[str, Any], now_utc: datetime | None = None) -> Dict[str, Any]:
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)

        tz = ZoneInfo(config["timezone"])
        local_now = now_utc.astimezone(tz)
        local_date = local_now.date()
        local_time = local_now.time()
        weekday = local_now.weekday()  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday

        open_t: time = config["open_time"]
        close_t: time = config["close_time"]

        open_dt = datetime.combine(local_date, open_t, tzinfo=tz)
        close_dt = datetime.combine(local_date, close_t, tzinfo=tz)

        is_weekday = weekday < 5
        status = "CLOSED"
        status_label = "Closed"
        badge_variant = "danger"

        # Check pre-market if applicable
        pre_open_dt = None
        if config.get("has_pre_market") and config.get("pre_market_open"):
            pre_open_dt = datetime.combine(local_date, config["pre_market_open"], tzinfo=tz)

        # Check after-hours if applicable
        after_close_dt = None
        if config.get("has_after_hours") and config.get("after_hours_close"):
            after_close_dt = datetime.combine(local_date, config["after_hours_close"], tzinfo=tz)

        progress_pct = 0.0
        countdown = ""
        countdown_label = ""
        next_event_time = ""

        if is_weekday:
            if open_t <= local_time < close_t:
                status = "OPEN"
                status_label = "Regular Market Open"
                badge_variant = "success"
                time_left = close_dt - local_now
                countdown = _format_timedelta(time_left)
                countdown_label = "Closes in"
                next_event_time = close_dt.strftime("%I:%M %p")

                total_session = (close_dt - open_dt).total_seconds()
                elapsed = (local_now - open_dt).total_seconds()
                progress_pct = min(100.0, max(0.0, round((elapsed / total_session) * 100, 1)))

            elif pre_open_dt and pre_open_dt <= local_now < open_dt:
                status = "PRE_MARKET"
                status_label = "Pre-Market"
                badge_variant = "warning"
                time_left = open_dt - local_now
                countdown = _format_timedelta(time_left)
                countdown_label = "Regular opens in"
                next_event_time = open_dt.strftime("%I:%M %p")

            elif after_close_dt and close_dt <= local_now < after_close_dt:
                status = "AFTER_HOURS"
                status_label = "After-Hours"
                badge_variant = "purple"
                time_left = after_close_dt - local_now
                countdown = _format_timedelta(time_left)
                countdown_label = "After-hours ends in"
                next_event_time = after_close_dt.strftime("%I:%M %p")

            elif local_time < open_t:
                status = "CLOSED"
                status_label = "Closed (Opens Today)"
                badge_variant = "danger"
                target_dt = pre_open_dt if pre_open_dt and local_now < pre_open_dt else open_dt
                time_left = target_dt - local_now
                countdown = _format_timedelta(time_left)
                countdown_label = "Opens in"
                next_event_time = target_dt.strftime("%I:%M %p")

            else:
                # Closed after regular hours on weekday
                status = "CLOSED"
                status_label = "Closed"
                badge_variant = "danger"
                # Next open is next morning (or Monday if Friday)
                days_ahead = 3 if weekday == 4 else 1
                next_day = local_date + timedelta(days=days_ahead)
                next_target = datetime.combine(next_day, open_t, tzinfo=tz)
                time_left = next_target - local_now
                countdown = _format_timedelta(time_left)
                countdown_label = f"Opens {next_day.strftime('%a')} in"
                next_event_time = next_target.strftime("%a %I:%M %p")
        else:
            # Weekend (Saturday or Sunday)
            status = "WEEKEND"
            status_label = "Weekend Closed"
            badge_variant = "secondary"
            days_to_monday = (7 - weekday) % 7
            if days_to_monday == 0:
                days_to_monday = 7
            next_monday = local_date + timedelta(days=days_to_monday)
            next_open_dt = datetime.combine(next_monday, open_t, tzinfo=tz)
            time_left = next_open_dt - local_now
            countdown = _format_timedelta(time_left)
            countdown_label = "Opens Monday in"
            next_event_time = f"Mon {next_open_dt.strftime('%I:%M %p')}"

        return {
            "id": config["id"],
            "name": config["name"],
            "short_name": config["short_name"],
            "region": config["region"],
            "flag": config["flag"],
            "timezone": config["timezone"],
            "tz_label": config["tz_label"],
            "local_date": local_date.strftime("%A, %b %d, %Y"),
            "local_time": local_now.strftime("%I:%M:%S %p"),
            "local_time_short": local_now.strftime("%I:%M %p"),
            "status": status,
            "status_label": status_label,
            "badge_variant": badge_variant,
            "is_open": status == "OPEN",
            "open_time": open_t.strftime("%I:%M %p"),
            "close_time": close_t.strftime("%I:%M %p"),
            "has_pre_market": config.get("has_pre_market", False),
            "pre_market_open": config["pre_market_open"].strftime("%I:%M %p") if config.get("pre_market_open") else None,
            "has_after_hours": config.get("has_after_hours", False),
            "after_hours_close": config["after_hours_close"].strftime("%I:%M %p") if config.get("after_hours_close") else None,
            "countdown": countdown,
            "countdown_label": countdown_label,
            "next_event_time": next_event_time,
            "progress_pct": progress_pct,
            "crypto_impact": config["crypto_impact"],
        }

    @classmethod
    def get_all_market_hours(cls) -> Dict[str, Any]:
        now_utc = datetime.now(timezone.utc)
        exchanges = [cls.get_exchange_status(cfg, now_utc=now_utc) for cfg in EXCHANGES_CONFIG]

        # Calculate crypto active liquidity session
        # Standard liquidity windows:
        # Asian Session: 00:00 - 08:00 UTC
        # London Session: 08:00 - 16:00 UTC
        # US Session: 13:00 - 21:00 UTC (peak volume during London/US overlap 13:00 - 16:00 UTC)
        utc_hour = now_utc.hour + now_utc.minute / 60.0
        active_sessions = []
        if 0 <= utc_hour < 8:
            active_sessions.append("Asian Liquidity Window")
        if 8 <= utc_hour < 16:
            active_sessions.append("European / London Session")
        if 13 <= utc_hour < 21:
            active_sessions.append("US Wall Street Session")
        if 21 <= utc_hour or utc_hour < 0:
            active_sessions.append("Overnight Inter-session")

        is_high_volatility = (13 <= utc_hour <= 17)  # US Open + London overlap

        open_count = sum(1 for e in exchanges if e["is_open"])

        return {
            "current_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "current_date": now_utc.strftime("%A, %B %d, %Y"),
            "open_count": open_count,
            "total_exchanges": len(exchanges),
            "crypto_market": {
                "status": "OPEN",
                "status_label": "24/7 Continuous Trading",
                "active_sessions": active_sessions,
                "is_peak_volatility": is_high_volatility,
                "volatility_tag": "High Volatility Overlap" if is_high_volatility else "Normal Trading Window",
                "description": "Cryptocurrency markets never sleep. Institutional ETF flow peaks during US regular hours (09:30 - 16:00 EST).",
            },
            "exchanges": exchanges,
        }

