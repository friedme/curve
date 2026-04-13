"""Read historical curve data from CSV snapshots.

Snapshot files live at data/snapshots/{slug}.csv with columns:
    snapshot_date, symbol, contract_date, label, tenor, price

This module finds the closest available snapshot to a requested date
and returns it in the same format as the live Barchart data.
"""

import csv
import os
from datetime import date
from pathlib import Path

SNAPSHOT_DIR = Path(os.environ.get("CURVE_DATA_DIR", Path(__file__).parent.parent.parent.parent / "data" / "snapshots"))


def get_available_dates(slug: str) -> list[date]:
    """Return sorted list of snapshot dates available for a commodity."""
    csv_path = SNAPSHOT_DIR / f"{slug}.csv"
    if not csv_path.exists():
        return []

    dates = set()
    with open(csv_path, "r", newline="") as f:
        for row in csv.DictReader(f):
            dates.add(date.fromisoformat(row["snapshot_date"]))
    return sorted(dates)


def find_closest_date(slug: str, target: date) -> date | None:
    """Find the snapshot date closest to (but not after) the target date."""
    available = get_available_dates(slug)
    if not available:
        return None

    # Find the latest date that is <= target
    best = None
    for d in available:
        if d <= target:
            best = d
        else:
            break

    # Only return a match if we found a date on or before target
    return best


def load_snapshot(slug: str, snapshot_date: date) -> list[dict] | None:
    """Load a curve snapshot for a specific date.

    Returns list of dicts matching the format used by the rest of the app:
        [{"tenor": 0, "label": "Apr 2026", "price": 101.76}, ...]

    Returns None if no snapshot file exists for this commodity.
    """
    csv_path = SNAPSHOT_DIR / f"{slug}.csv"
    if not csv_path.exists():
        return None

    points = []
    with open(csv_path, "r", newline="") as f:
        for row in csv.DictReader(f):
            if row["snapshot_date"] == snapshot_date.isoformat():
                points.append({
                    "tenor": int(row["tenor"]),
                    "label": row["label"],
                    "price": float(row["price"]),
                })

    return points if points else None
