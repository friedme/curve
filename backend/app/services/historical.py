"""Historical forward curve reconstruction using yfinance.

Strategy: Take the CURRENT live chain from Barchart (contracts that are still
active today), and look up what their prices were on the historical date.
This avoids the problem of expired contracts being delisted from Yahoo Finance.

The result is the historical price of each currently-active contract, aligned
by tenor to the current curve.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import yfinance as yf
from cachetools import TTLCache

from app.services.barchart import fetch_futures_chain

# Historical data is immutable, cache for 24h
_cache: TTLCache = TTLCache(maxsize=5000, ttl=86400)
_executor = ThreadPoolExecutor(max_workers=10)

# Barchart symbol -> yfinance symbol mapping
# Barchart uses different roots than Yahoo for some commodities
_SYMBOL_MAP = {
    "CB": "BZ",   # Brent: CB on Barchart, BZ on Yahoo
    "TG": "TTF",  # TTF: TG on Barchart, TTF on Yahoo
    "LQ": "MTF",  # Newcastle Coal: LQ on Barchart, MTF on Yahoo
}

_EXCHANGE_MAP = {
    "CL": "NYM", "BZ": "NYM", "NG": "NYM", "TTF": "NYM",
    "HG": "CMX", "GC": "CMX", "SI": "CMX",
    "MTF": "NYM", "UX": "NYM", "U7": "SGX",
}


def _barchart_to_yfinance(barchart_symbol: str, barchart_root: str) -> str | None:
    """Convert a Barchart symbol like 'CBK26' to yfinance format 'BZK26.NYM'."""
    suffix = barchart_symbol[len(barchart_root):]  # e.g. "K26"
    yf_root = _SYMBOL_MAP.get(barchart_root, barchart_root)
    exchange = _EXCHANGE_MAP.get(yf_root)
    if not exchange:
        return None
    return f"{yf_root}{suffix}.{exchange}"


def _fetch_price_on_date(ticker: str, target_date: date) -> float | None:
    """Fetch closing price on or near a specific date."""
    cache_key = f"{ticker}_{target_date.isoformat()}"
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        t = yf.Ticker(ticker)
        start = target_date - timedelta(days=5)
        end = target_date + timedelta(days=1)
        hist = t.history(start=start.isoformat(), end=end.isoformat())
        if hist.empty:
            _cache[cache_key] = None
            return None
        valid = hist[hist.index.date <= target_date]
        if valid.empty:
            valid = hist
        price = float(valid["Close"].iloc[-1])
        _cache[cache_key] = price
        return price
    except Exception:
        _cache[cache_key] = None
        return None


async def fetch_historical_curve(
    barchart_root: str, historical_date: date
) -> list[dict]:
    """Look up what today's active contracts were priced at on a historical date.

    Uses the current Barchart chain to get the list of active contracts,
    then fetches their prices from Yahoo Finance at the historical date.
    Contracts that didn't exist yet or have no data are skipped.
    """
    current_chain = fetch_futures_chain(barchart_root)
    if not current_chain:
        return []

    loop = asyncio.get_event_loop()

    async def fetch_one(contract: dict) -> dict | None:
        yf_ticker = _barchart_to_yfinance(contract["symbol"], barchart_root)
        if not yf_ticker:
            return None
        price = await loop.run_in_executor(
            _executor, _fetch_price_on_date, yf_ticker, historical_date
        )
        if price is None:
            return None
        return {
            "tenor": contract["tenor"],
            "label": contract["label"],
            "price": price,
        }

    # Limit to first 36 contracts to avoid excessive API calls
    tasks = [fetch_one(c) for c in current_chain[:36]]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]
