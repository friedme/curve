#!/usr/bin/env python3
"""Daily snapshot of commodity forward curves from Barchart.

Saves each commodity's futures chain as a clean, append-only CSV file.
Designed to be run once per day (e.g., via cron or Task Scheduler).

Output format (one CSV per commodity):
    data/snapshots/{slug}.csv

CSV columns:
    snapshot_date  – date the snapshot was taken (YYYY-MM-DD)
    symbol         – exchange symbol (e.g., CLJ26)
    contract_date  – delivery month (YYYY-MM-01)
    label          – human-readable label (e.g., "Apr 2026")
    tenor          – months forward from front contract (0, 1, 2, ...)
    price          – last traded price

Usage:
    python snapshot.py                  # snapshot all commodities
    python snapshot.py wti brent        # snapshot specific slugs
    python snapshot.py --list           # list available commodities
    python snapshot.py --dir /my/path   # custom output directory
"""

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

# Add the backend app to the path so we can import from it
sys.path.insert(0, str(Path(__file__).parent))

from app.config import COMMODITIES, DataQuality
from app.services.barchart import fetch_futures_chain

DEFAULT_DIR = Path(__file__).parent.parent / "data" / "snapshots"

CSV_COLUMNS = ["snapshot_date", "symbol", "contract_date", "label", "tenor", "price"]


def snapshot_commodity(slug: str, output_dir: Path, snapshot_date: date) -> int:
    """Fetch and append today's curve for one commodity. Returns row count."""
    config = COMMODITIES.get(slug)
    if not config or config.data_quality == DataQuality.UNAVAILABLE:
        return 0

    chain = fetch_futures_chain(config.barchart_root)
    if not chain:
        print(f"  {slug}: no data returned")
        return 0

    csv_path = output_dir / f"{slug}.csv"
    file_exists = csv_path.exists()

    # Check if we already have a snapshot for this date
    if file_exists:
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("snapshot_date") == snapshot_date.isoformat():
                    print(f"  {slug}: already snapshotted for {snapshot_date}")
                    return 0

    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        for c in chain:
            writer.writerow({
                "snapshot_date": snapshot_date.isoformat(),
                "symbol": c["symbol"],
                "contract_date": c["contract_date"],
                "label": c["label"],
                "tenor": c["tenor"],
                "price": c["price"],
            })

    return len(chain)


def main():
    parser = argparse.ArgumentParser(description="Snapshot commodity forward curves")
    parser.add_argument("slugs", nargs="*", help="Commodity slugs to snapshot (default: all)")
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR, help="Output directory")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(),
                        help="Snapshot date (default: today)")
    parser.add_argument("--list", action="store_true", help="List available commodities")
    args = parser.parse_args()

    if args.list:
        for slug, config in COMMODITIES.items():
            status = "available" if config.barchart_root else "unavailable"
            print(f"  {slug:<20s} {config.display_name:<30s} [{status}]")
        return

    args.dir.mkdir(parents=True, exist_ok=True)

    slugs = args.slugs or [
        s for s, c in COMMODITIES.items()
        if c.data_quality != DataQuality.UNAVAILABLE
    ]

    print(f"Snapshotting {len(slugs)} commodities for {args.date} -> {args.dir}")
    total = 0
    for slug in slugs:
        n = snapshot_commodity(slug, args.dir, args.date)
        if n:
            print(f"  {slug}: {n} contracts")
            total += n

    print(f"Done. {total} total rows written.")


if __name__ == "__main__":
    main()
