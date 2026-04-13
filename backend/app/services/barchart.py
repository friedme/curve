"""Barchart data fetcher for commodity futures chains.

Fetches live forward curve data from Barchart's internal API.
Session cookies are obtained by visiting the main page first.
"""

import re
from datetime import date, datetime
from urllib.parse import unquote

import requests
from cachetools import TTLCache

from app.config import MONTH_CODE_TO_NUM

# Cache the session (valid for ~30 min typically)
_session_cache: TTLCache = TTLCache(maxsize=1, ttl=1800)
# Cache curve results: 5 min for live data
_curve_cache: TTLCache = TTLCache(maxsize=50, ttl=300)

_MONTH_YEAR_RE = re.compile(r"^([FGHJKMNQUVXZ])(\d{2})$")


def _get_session() -> requests.Session:
    if "session" in _session_cache:
        return _session_cache["session"]

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html",
    })

    # Visit a page to obtain session cookies
    session.get("https://www.barchart.com/futures/quotes/CL*0/futures-prices")

    # Set up for API calls
    xsrf = session.cookies.get("XSRF-TOKEN")
    if xsrf:
        session.headers["X-XSRF-TOKEN"] = unquote(xsrf)
    session.headers["Accept"] = "application/json"
    session.headers["Referer"] = "https://www.barchart.com/futures/quotes/CL*0/futures-prices"

    _session_cache["session"] = session
    return session


def _parse_contract_date(symbol: str, root: str) -> date | None:
    """Parse contract month/year from symbol like 'CLJ26' -> April 2026."""
    suffix = symbol[len(root):]  # e.g. "J26" from "CLJ26" or "U7J26"
    m = _MONTH_YEAR_RE.match(suffix)
    if not m:
        return None
    month_code, year_str = m.group(1), m.group(2)
    month = MONTH_CODE_TO_NUM.get(month_code)
    if month is None:
        return None
    year = 2000 + int(year_str)
    return date(year, month, 1)


def fetch_futures_chain(barchart_root: str) -> list[dict]:
    """Fetch the full futures chain for a commodity from Barchart.

    Returns a list of dicts sorted by contract date:
    [{"symbol": "CLJ26", "price": 101.76, "contract_date": "2026-04-01", "label": "Apr 2026", "tenor": 0}, ...]

    The `tenor` field is the month offset from the front contract (0, 1, 2, ...).
    """
    cache_key = barchart_root
    if cache_key in _curve_cache:
        return _curve_cache[cache_key]

    session = _get_session()
    api_url = "https://www.barchart.com/proxies/core-api/v1/quotes/get"
    params = {
        "list": "futures.contractInRoot",
        "fields": "symbol,symbolName,lastPrice,volume,openInterest,tradeTime",
        "root": barchart_root,
        "raw": "1",
    }

    try:
        r = session.get(api_url, params=params, timeout=15)
        if r.status_code == 401:
            # Session expired, clear cache and retry once
            _session_cache.clear()
            session = _get_session()
            r = session.get(api_url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception:
        # Connection error, HTTP error, or non-JSON response (e.g. captcha page)
        _session_cache.clear()
        return []
    contracts = []

    for row in data.get("data", []):
        raw = row.get("raw", {})
        symbol = raw.get("symbol", "")
        price = raw.get("lastPrice")

        if not symbol or price is None or price <= 0:
            continue

        # Skip the continuous contract (e.g., CLY00)
        if symbol.endswith("Y00"):
            continue

        contract_date = _parse_contract_date(symbol, barchart_root)
        if contract_date is None:
            continue

        # Skip expired contracts (before current month)
        today = date.today()
        if contract_date < today.replace(day=1):
            continue

        contracts.append({
            "symbol": symbol,
            "price": float(price),
            "contract_date": contract_date.isoformat(),
            "label": contract_date.strftime("%b %Y"),
        })

    # Sort by contract date
    contracts.sort(key=lambda c: c["contract_date"])

    # Assign tenor (month offset from front)
    for i, c in enumerate(contracts):
        c["tenor"] = i

    _curve_cache[cache_key] = contracts
    return contracts
