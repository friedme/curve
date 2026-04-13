from pydantic import BaseModel
from typing import Optional


class CurvePoint(BaseModel):
    tenor: int
    label: str
    price: float


class ForwardCurveResponse(BaseModel):
    commodity: str
    slug: str
    data_quality: str
    unit: str
    as_of: Optional[str] = None
    points: list[CurvePoint]
    total_contracts: int = 0
    fallback_etf: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None


class CommodityListItem(BaseModel):
    slug: str
    display_name: str
    data_quality: str
    unit: str


class SpreadPoint(BaseModel):
    tenor: int
    current_label: str
    historical_label: str
    diff: float


class CurveComparisonResponse(BaseModel):
    current: ForwardCurveResponse
    historical: ForwardCurveResponse
    spread: list[SpreadPoint]


class SpotPriceItem(BaseModel):
    slug: str
    display_name: str
    unit: str
    price: float
    contract: str  # e.g. "Apr 2026"


class DatedCurve(BaseModel):
    as_of: str
    label: str  # e.g. "Current", "1M ago"
    points: list[CurvePoint]


class CurveEvolutionResponse(BaseModel):
    commodity: str
    slug: str
    unit: str
    curves: list[DatedCurve]


class SpreadSeriesPoint(BaseModel):
    date: str
    m1_m6: Optional[float] = None
    m1_m12: Optional[float] = None


class SpreadHistoryResponse(BaseModel):
    commodity: str
    slug: str
    unit: str
    points: list[SpreadSeriesPoint]
