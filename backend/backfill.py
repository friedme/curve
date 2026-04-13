#!/usr/bin/env python3
"""One-time backfill of front-month (tenor 0) prices from yfinance.

This fetches the continuous front-month contract history (e.g. CL=F)
and saves one data point per trading day. Unlike the deleted historical.py,
this is accurate — it's a single continuous series, not a reconstructed curve.

Usage:
    python backfill.py                # backfill all, 1 year
    python backfill.py --days 365     # custom lookback
    python backfill.py wti brent      # specific commodities
"""

import argparse
import csv
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent))

from app.config import COMMODITIES, DataQuality

DEFAULT_DIR = Path(os.environ.get("CURVE_DATA_DIR", Path(__file__).parent.parent / "data" / "snapshots"))

CSV_COLUMNS = ["snapshot_date", "symbol", "contract_date", "label", "tenor", "price"]

# Barchart root -> yfinance continuous front-month ticker
YF_FRONT_MONTH = {
    "CL": "CL=F",     # WTI
    "CB": "BZ=F",     # Brent
    "NG": "NG=F",     # Henry Hub
    "TG": "TTF=F",    # TTF
    "LQ": "MTF=F",    # Newcastle Coal
    "U7": None,       # Met Coal — no reliable yfinance ticker
    "JC": None,       # Urea — no reliable yfinance ticker
}


def get_existing_dates(csv_path: Path) -> set[str]:
    """Read all snapshot_date values already in the CSV."""
    if not csv_path.exists():
        return set()
    dates = set()
    with open(csv_path, "r", newline="") as f:
        for row in csv.DictReader(f):
            dates.add(row["snapshot_date"])
    return dates


def backfill_commodity(slug: str, output_dir: Path, days: int) -> int:
    config = COMMODITIES.get(slug)
    if not config or config.data_quality == DataQuality.UNAVAILABLE:
        return 0

    ticker_symbol = YF_FRONT_MONTH.get(config.barchart_root)
    if not ticker_symbol:
        print(f"  {slug}: no yfinance front-month ticker, skipping")
        return 0

    print(f"  {slug}: fetching {ticker_symbol} ({days}d)...", end=" ", flush=True)

    try:
        ticker = yf.Ticker(ticker_symbol)
        start = date.today() - timedelta(days=days)
        hist = ticker.history(start=start.isoformat(), end=date.today().isoformat())
    except Exception as e:
        print(f"error: {e}")
        return 0

    if hist.empty:
        print("no data")
        return 0

    csv_path = output_dir / f"{slug}.csv"
    existing = get_existing_dates(csv_path)
    file_exists = csv_path.exists()

    rows_written = 0
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()

        for ts, row in hist.iterrows():
            snap_date = ts.date().isoformat()
            if snap_date in existing:
                continue

            price = float(row["Close"])
            if price <= 0:
                continue

            # Front-month only: tenor 0, label from the date
            month_label = ts.strftime("%b %Y")
            writer.writerow({
                "snapshot_date": snap_date,
                "symbol": ticker_symbol,
                "contract_date": ts.strftime("%Y-%m-01"),
                "label": month_label,
                "tenor": 0,
                "price": round(price, 2),
            })
            rows_written += 1

    print(f"{rows_written} days added")
    return rows_written


def main():
    parser = argparse.ArgumentParser(description="Backfill front-month prices from yfinance")
    parser.add_argument("slugs", nargs="*", help="Commodity slugs (default: all)")
    parser.add_argument("--days", type=int, default=365, help="Lookback in days (default: 365)")
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR, help="Output directory")
    args = parser.parse_args()

    args.dir.mkdir(parents=True, exist_ok=True)

    slugs = args.slugs or [
        s for s, c in COMMODITIES.items()
        if c.data_quality != DataQuality.UNAVAILABLE
    ]

    print(f"Backfilling front-month prices ({args.days}d) -> {args.dir}")
    total = 0
    for slug in slugs:
        total += backfill_commodity(slug, args.dir, args.days)

    print(f"Done. {total} total rows written.")


if __name__ == "__main__":
    main()
