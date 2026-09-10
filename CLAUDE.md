# CLAUDE.md — curve (commodity forward curves)

Web app showing commodity forward curves (WTI, Brent, Henry Hub, TTF, Newcastle coal,
met coal, urea) plus spot tiles (gold, silver, copper, uranium). The live curve comes from
Barchart; history comes from daily CSV snapshots taken on the Pi.

## Stack & layout

- Backend: FastAPI (`backend/app`), Python 3.12. Serves the API and, in production, the built
  frontend from `CURVE_STATIC_DIR`.
- Frontend: React + Vite + Tailwind + TypeScript (`frontend/src`). Dev server on :5173 proxies
  `/api` to :8001.
- `backend/app/services/barchart.py` — all Barchart access (live futures chains).
- `backend/app/services/curve_builder.py` — live curve, or closest snapshot on/before a date.
- `backend/app/services/snapshots.py` — reads `data/snapshots/{slug}.csv`.
- `backend/app/routers/curves.py` — endpoints; lookbacks (1W/1M/3M/6M/1Y) are in `LOOKBACKS`.
- `backend/app/config.py` — commodity list, Barchart roots, spot watches.
- `backend/snapshot.py` — nightly snapshot job. `backend/backfill.py` — see warning below.
- `backend/app/services/data_fetcher.py` and `ticker_builder.py` are unused (nothing imports them).

## Barchart access (important)

Since ~2026-08-29 barchart.com is behind an AWS WAF JavaScript challenge. Plain `requests`
and `curl_cffi` (TLS impersonation) get an empty 202 and the API returns 403. Replaying the
browser's cookies in `requests` also gets 403.

What works: a headless Chromium (Playwright) page on barchart.com solves the challenge, and
the API calls are made **from inside that page** via `fetch()`. `barchart.py` keeps one page
open on a dedicated thread (Playwright's sync API is thread-bound and can't run in the
asyncio loop) and recycles it every 20 min or on any failure. Don't "simplify" this back to
requests. If Barchart breaks again, first test from the Windows PC with a scratch script to
see whether the WAF behaviour changed before touching the Pi.

`fetch_futures_chain` returns `[]` on failure and logs the error — the UI then shows no
"Current" curve.

## Data

- Snapshot CSV columns: `snapshot_date, symbol, contract_date, label, tenor, price`.
  One file per commodity, append-only, full chain per day.
- History starts 2026-04-13. **Gap: 2026-08-29 → 2026-09-09 is missing** (Barchart block)
  and can't be recovered — Barchart only serves current quotes. Don't fill it with
  interpolated or fabricated values.
- Historical curves report `as_of` = the snapshot date actually used, not the requested date.
- 6M ago appears automatically from ~2026-10-12, 1Y ago from ~2027-04-13.
- **Don't run `backfill.py` into the live data.** It writes front-month-only (tenor 0) rows
  from yfinance; those would make old lookbacks render as a single dot instead of a curve.

## Deployment (Raspberry Pi)

- Repo on the Pi: `/home/fried/curve`, SSH as `fried@192.168.1.49` (host `homepi`, aarch64).
- One image `curve-app:latest` shared by both compose services: `web` (container
  `curve-web-1`, port 8001) and `snapshot` (profile `tools`, run on demand). Snapshots live
  in the named volume `curve_curve-data`. Chromium needs `shm_size: 512m`.
- Base image is pinned to `python:3.12-slim-bookworm` because Playwright's `--with-deps`
  officially supports Debian 12.
- Deploy: push to GitHub from Windows, then on the Pi `./deploy.sh`
  (`git pull --ff-only && docker compose up -d --build`).
- Pi crontab (not in the repo):
  - `0 22 * * *` — `docker compose run --rm snapshot`, log in `/tmp/curve-snapshot.log`.
    Exits 1 and prints `FAILED: ...` if any commodity returned no data.
  - `30 22 * * *` — pulls the repo, copies the snapshots out of `curve-web-1` into
    `data/snapshots/`, commits "Daily snapshot data" and pushes. So GitHub is the backup, and
    the local Windows clone is always behind — `git pull` before committing.

## Local dev (Windows)

```powershell
cd backend; pip install -r requirements.txt; python -m playwright install chromium-headless-shell
cd ..\frontend; npm install
cd ..; python run.py        # backend :8001 + frontend :5173
```
