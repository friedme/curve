import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import yfinance as yf
from cachetools import TTLCache

# Current prices: 5 min TTL, up to 500 entries
_current_cache: TTLCache = TTLCache(maxsize=500, ttl=300)
# Historical prices: 24h TTL
_historical_cache: TTLCache = TTLCache(maxsize=2000, ttl=86400)

_executor = ThreadPoolExecutor(max_workers=8)


def _fetch_single_current(ticker: str) -> float | None:
    if ticker in _current_cache:
        return _current_cache[ticker]
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if hist.empty:
            return None
        price = float(hist["Close"].iloc[-1])
        _current_cache[ticker] = price
        return price
    except Exception:
        return None


def _fetch_single_historical(ticker: str, target_date: date) -> float | None:
    cache_key = f"{ticker}_{target_date.isoformat()}"
    if cache_key in _historical_cache:
        return _historical_cache[cache_key]
    try:
        t = yf.Ticker(ticker)
        start = target_date - timedelta(days=5)
        end = target_date + timedelta(days=1)
        hist = t.history(start=start.isoformat(), end=end.isoformat())
        if hist.empty:
            return None
        valid = hist[hist.index.date <= target_date]
        if valid.empty:
            valid = hist
        price = float(valid["Close"].iloc[-1])
        _historical_cache[cache_key] = price
        return price
    except Exception:
        return None


async def fetch_curve_prices(
    tickers: list[dict],
    historical_date: date | None = None,
) -> list[dict]:
    """Fetch prices for a list of contract tickers concurrently."""
    loop = asyncio.get_event_loop()

    async def fetch_one(contract: dict) -> dict:
        ticker = contract["ticker"]
        if historical_date:
            price = await loop.run_in_executor(
                _executor, _fetch_single_historical, ticker, historical_date
            )
        else:
            price = await loop.run_in_executor(
                _executor, _fetch_single_current, ticker
            )
        return {**contract, "price": price}

    tasks = [fetch_one(c) for c in tickers]
    return await asyncio.gather(*tasks)
