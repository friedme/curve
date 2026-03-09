import logging
from datetime import date

from app.config import COMMODITIES, DataQuality
from app.services.barchart import fetch_futures_chain
from app.services.historical import fetch_historical_curve
from app.services.snapshots import find_closest_date, load_snapshot

log = logging.getLogger(__name__)


async def build_forward_curve(
    commodity_slug: str,
    historical_date: date | None = None,
) -> dict:
    config = COMMODITIES[commodity_slug]

    if config.data_quality == DataQuality.UNAVAILABLE:
        return {
            "commodity": config.display_name,
            "slug": config.slug,
            "data_quality": config.data_quality.value,
            "unit": config.unit,
            "as_of": (historical_date or date.today()).isoformat(),
            "points": [],
            "total_contracts": 0,
            "fallback_etf": config.fallback_etf,
            "message": f"No futures data available for {config.display_name}.",
        }

    source = "live"

    if historical_date:
        # Try local CSV snapshots first (exact or closest earlier date)
        snap_date = find_closest_date(commodity_slug, historical_date)
        points = None
        if snap_date:
            points = load_snapshot(commodity_slug, snap_date)
            if points:
                source = "snapshot"
                log.info(
                    "Using snapshot %s for %s (requested %s)",
                    snap_date, commodity_slug, historical_date,
                )

        # Fall back to yfinance if no snapshot available
        if not points:
            points = await fetch_historical_curve(config.barchart_root, historical_date)
            source = "yfinance"
    else:
        chain = fetch_futures_chain(config.barchart_root)
        points = [
            {
                "tenor": c["tenor"],
                "label": c["label"],
                "price": c["price"],
            }
            for c in chain
        ]

    return {
        "commodity": config.display_name,
        "slug": config.slug,
        "data_quality": config.data_quality.value,
        "unit": config.unit,
        "as_of": (historical_date or date.today()).isoformat(),
        "points": points,
        "total_contracts": len(points),
        "source": source,
    }
