import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from functools import lru_cache

import yfinance as yf
from cachetools import TTLCache
from fastapi import APIRouter, HTTPException, Query

from app.config import COMMODITIES, SPOT_WATCHES
from app.models.schemas import (
    CommodityListItem,
    CurveComparisonResponse,
    ForwardCurveResponse,
    SpotPriceItem,
    SpreadPoint,
)
from app.services.barchart import fetch_futures_chain
from app.services.curve_builder import build_forward_curve

_executor = ThreadPoolExecutor(max_workers=4)
_spot_history_cache: TTLCache = TTLCache(maxsize=20, ttl=3600)  # 1hr cache

router = APIRouter(prefix="/api", tags=["curves"])


@router.get("/commodities", response_model=list[CommodityListItem])
async def list_commodities():
    return [
        CommodityListItem(
            slug=c.slug,
            display_name=c.display_name,
            data_quality=c.data_quality.value,
            unit=c.unit,
        )
        for c in COMMODITIES.values()
    ]


@router.get("/curve/{commodity_slug}", response_model=ForwardCurveResponse)
async def get_forward_curve(commodity_slug: str):
    if commodity_slug not in COMMODITIES:
        raise HTTPException(404, f"Unknown commodity: {commodity_slug}")
    return await build_forward_curve(commodity_slug)


@router.get("/curve/{commodity_slug}/compare", response_model=CurveComparisonResponse)
async def compare_curves(
    commodity_slug: str,
    historical_date: date = Query(..., description="YYYY-MM-DD"),
):
    if commodity_slug not in COMMODITIES:
        raise HTTPException(404, f"Unknown commodity: {commodity_slug}")

    current = await build_forward_curve(commodity_slug)
    historical = await build_forward_curve(commodity_slug, historical_date=historical_date)

    # Compute spread by matching on TENOR (months forward), not label.
    # This compares "1-month forward then" vs "1-month forward now".
    hist_by_tenor = {p["tenor"]: p for p in historical["points"]}
    spread = []
    for pt in current["points"]:
        hist_pt = hist_by_tenor.get(pt["tenor"])
        if hist_pt:
            spread.append(SpreadPoint(
                tenor=pt["tenor"],
                current_label=pt["label"],
                historical_label=hist_pt["label"],
                diff=round(pt["price"] - hist_pt["price"], 4),
            ))

    return CurveComparisonResponse(
        current=ForwardCurveResponse(**current),
        historical=ForwardCurveResponse(**historical),
        spread=spread,
    )


@router.get("/spot-prices", response_model=list[SpotPriceItem])
async def get_spot_prices():
    """Front-month prices for commodities tracked as spot watches."""
    results = []
    for watch in SPOT_WATCHES:
        chain = fetch_futures_chain(watch.barchart_root)
        if chain:
            front = chain[0]
            results.append(SpotPriceItem(
                slug=watch.slug,
                display_name=watch.display_name,
                unit=watch.unit,
                price=front["price"],
                contract=front["label"],
            ))
    return results


def _fetch_spot_history(ticker: str, period: str) -> list[dict]:
    """Fetch historical prices — yfinance or FRED depending on ticker prefix."""
    cache_key = f"{ticker}:{period}"
    if cache_key in _spot_history_cache:
        return _spot_history_cache[cache_key]

    if ticker.startswith("FRED:"):
        points = _fetch_fred_history(ticker.split(":", 1)[1], period)
    else:
        points = _fetch_yfinance_history(ticker, period)

    _spot_history_cache[cache_key] = points
    return points


def _fetch_yfinance_history(ticker: str, period: str) -> list[dict]:
    """Blocking yfinance call."""
    t = yf.Ticker(ticker)
    df = t.history(period=period)
    if df.empty:
        return []

    points = []
    for dt, row in df.iterrows():
        points.append({
            "date": dt.strftime("%Y-%m-%d"),
            "price": round(float(row["Close"]), 4),
        })
    return points


def _fetch_fred_history(series_id: str, period: str) -> list[dict]:
    """Fetch from FRED CSV endpoint (free, no API key)."""
    import requests as req
    from datetime import datetime, timedelta

    period_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825}
    days = period_map.get(period, 365)
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start}"
    r = req.get(url, timeout=10)
    if r.status_code != 200:
        return []

    points = []
    for line in r.text.strip().split("\n")[1:]:  # skip header
        parts = line.split(",")
        if len(parts) == 2 and parts[1] != ".":
            try:
                points.append({
                    "date": parts[0],
                    "price": round(float(parts[1]), 2),
                })
            except ValueError:
                continue
    return points


@router.get("/spot-history/{slug}")
async def get_spot_history(
    slug: str,
    period: str = Query("1y", description="1mo, 3mo, 6mo, 1y, 2y, 5y"),
):
    """Historical daily prices for a spot-watch commodity (via Yahoo Finance)."""
    watch = next((w for w in SPOT_WATCHES if w.slug == slug), None)
    if not watch:
        raise HTTPException(404, f"Unknown spot commodity: {slug}")

    if period not in ("1mo", "3mo", "6mo", "1y", "2y", "5y"):
        raise HTTPException(400, "Invalid period")

    loop = asyncio.get_event_loop()
    points = await loop.run_in_executor(
        _executor, _fetch_spot_history, watch.yfinance_ticker, period
    )

    return {
        "slug": watch.slug,
        "display_name": watch.display_name,
        "unit": watch.unit,
        "period": period,
        "points": points,
        "history_label": watch.history_label or None,
    }
