from dataclasses import dataclass
from enum import Enum
from typing import Optional


MONTH_CODES = {
    1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
    7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z",
}

MONTH_CODE_TO_NUM = {v: k for k, v in MONTH_CODES.items()}


class DataQuality(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


@dataclass
class CommodityConfig:
    slug: str
    display_name: str
    barchart_root: str
    unit: str
    data_quality: DataQuality
    fallback_etf: Optional[str] = None


@dataclass
class SpotWatch:
    """A commodity to show as a spot-price-only tile (no forward curve)."""
    slug: str
    display_name: str
    barchart_root: str
    unit: str
    yfinance_ticker: str  # for historical price chart
    history_label: str = ""  # override chart label if ticker is a proxy (e.g. ETF)


# ── Forward curve commodities ──────────────────────────────────────
COMMODITIES: dict[str, CommodityConfig] = {
    "wti": CommodityConfig(
        slug="wti", display_name="WTI Crude Oil",
        barchart_root="CL", unit="USD/bbl", data_quality=DataQuality.FULL,
    ),
    "brent": CommodityConfig(
        slug="brent", display_name="Brent Crude Oil",
        barchart_root="CB", unit="USD/bbl", data_quality=DataQuality.FULL,
    ),
    "henry-hub": CommodityConfig(
        slug="henry-hub", display_name="Henry Hub Natural Gas",
        barchart_root="NG", unit="USD/MMBtu", data_quality=DataQuality.FULL,
    ),
    "ttf": CommodityConfig(
        slug="ttf", display_name="Dutch TTF Natural Gas",
        barchart_root="TG", unit="EUR/MWh", data_quality=DataQuality.FULL,
    ),
    "newcastle-coal": CommodityConfig(
        slug="newcastle-coal", display_name="Newcastle Coal",
        barchart_root="LQ", unit="USD/t", data_quality=DataQuality.FULL,
    ),
    "met-coal": CommodityConfig(
        slug="met-coal", display_name="Met Coal (Coking)",
        barchart_root="U7", unit="USD/t", data_quality=DataQuality.FULL,
    ),
    "urea": CommodityConfig(
        slug="urea", display_name="Urea (FOB US Gulf)",
        barchart_root="JC", unit="USD/st", data_quality=DataQuality.FULL,
    ),
}

# ── Spot price watches (front-month proxy, no curve) ───────────────
SPOT_WATCHES: list[SpotWatch] = [
    SpotWatch(slug="gold", display_name="Gold", barchart_root="GC", unit="USD/oz", yfinance_ticker="GC=F"),
    SpotWatch(slug="silver", display_name="Silver", barchart_root="SI", unit="USD/oz", yfinance_ticker="SI=F"),
    SpotWatch(slug="copper", display_name="Copper", barchart_root="HG", unit="USD/lb", yfinance_ticker="HG=F"),
    SpotWatch(slug="uranium", display_name="Uranium", barchart_root="UX", unit="USD/lb", yfinance_ticker="FRED:PURANUSDM", history_label="IMF/FRED monthly"),
]
