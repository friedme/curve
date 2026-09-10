"""Barchart data fetcher for commodity futures chains.

Fetches live forward curve data from Barchart's internal API.

Since late Aug 2026 barchart.com sits behind an AWS WAF JavaScript challenge:
plain HTTP clients get an empty 202 and every API call returns 403. So we keep
a headless Chromium page open on barchart.com (it solves the challenge like a
normal browser) and issue the API calls from inside that page via fetch().
Replaying the browser's cookies in `requests` does not work — the WAF still
returns 403 — so the calls must stay in the browser.
"""

import atexit
import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from cachetools import TTLCache

from app.config import MONTH_CODE_TO_NUM

log = logging.getLogger(__name__)

# Cache curve results: 5 min for live data
_curve_cache: TTLCache = TTLCache(maxsize=50, ttl=300)
_cache_lock = threading.Lock()

_MONTH_YEAR_RE = re.compile(r"^([FGHJKMNQUVXZ])(\d{2})$")

PAGE_URL = "https://www.barchart.com/futures/quotes/CL*0/futures-prices"
API_PATH = "/proxies/core-api/v1/quotes/get"
FIELDS = "symbol,symbolName,lastPrice,volume,openInterest,tradeTime"

# Recycle the browser page periodically so WAF/session tokens never go stale.
PAGE_MAX_AGE_S = 20 * 60
CHALLENGE_TIMEOUT_S = 60

_FETCH_JS = """
async ([path, params]) => {
    const m = document.cookie.match(/(?:^|; )XSRF-TOKEN=([^;]+)/);
    const headers = {'Accept': 'application/json'};
    if (m) headers['X-XSRF-TOKEN'] = decodeURIComponent(m[1]);
    const r = await fetch(path + '?' + new URLSearchParams(params), {headers});
    return {status: r.status, body: await r.text()};
}
"""


class BarchartBlocked(Exception):
    pass


class _BrowserClient:
    """Headless Chromium owned by one dedicated thread.

    Playwright's sync API is bound to the thread that started it and refuses to
    run inside an asyncio loop, so every browser call is funnelled through a
    single-worker executor. Callers (FastAPI handlers, snapshot.py) just block
    on the result, same as they did with requests.
    """

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="barchart-browser")
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None
        self._page_opened_at = 0.0

    def get_json(self, params: dict) -> dict:
        return self._executor.submit(self._get_json, params).result(timeout=180)

    def close(self):
        try:
            self._executor.submit(self._shutdown).result(timeout=30)
        except Exception:
            pass

    # --- everything below runs on the browser thread ---

    def _get_json(self, params: dict) -> dict:
        for attempt in (1, 2):
            try:
                self._ensure_page()
                res = self._page.evaluate(_FETCH_JS, [API_PATH, params])
                if res["status"] == 200:
                    return json.loads(res["body"])
                raise BarchartBlocked(f"API HTTP {res['status']}: {res['body'][:200]}")
            except Exception as e:
                log.warning("Barchart fetch attempt %d for %s failed: %s", attempt, params.get("root"), e)
                self._close_page()
                if attempt == 2:
                    raise

    def _ensure_page(self):
        if self._page and time.time() - self._page_opened_at < PAGE_MAX_AGE_S:
            return
        self._close_page()

        if self._browser is None:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True)

        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1366, "height": 768},
        )
        # Images/fonts/media aren't needed for the challenge or the API.
        self._context.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in ("image", "media", "font")
            else route.continue_(),
        )
        page = self._context.new_page()
        t0 = time.time()
        page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=CHALLENGE_TIMEOUT_S * 1000)

        # The first response is the WAF challenge; once solved the browser gets an
        # aws-waf-token and reloads into the real page, which sets Barchart's own
        # session cookie. Wait for both before using the page.
        while True:
            names = {c["name"] for c in self._context.cookies()}
            if "aws-waf-token" in names and "laravel_session" in names:
                break
            if time.time() - t0 > CHALLENGE_TIMEOUT_S:
                raise BarchartBlocked(f"WAF challenge not solved within {CHALLENGE_TIMEOUT_S}s (cookies: {sorted(names)})")
            page.wait_for_timeout(500)
        page.wait_for_load_state("domcontentloaded")

        log.info("Barchart browser session ready in %.1fs", time.time() - t0)
        self._page = page
        self._page_opened_at = time.time()

    def _close_page(self):
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
        self._context = None
        self._page = None

    def _shutdown(self):
        self._close_page()
        for obj, method in ((self._browser, "close"), (self._pw, "stop")):
            if obj is not None:
                try:
                    getattr(obj, method)()
                except Exception:
                    pass
        self._browser = None
        self._pw = None


_client = _BrowserClient()
atexit.register(_client.close)


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
    Returns [] if Barchart can't be reached (the failure is logged).
    """
    cache_key = barchart_root
    with _cache_lock:
        if cache_key in _curve_cache:
            return _curve_cache[cache_key]

    params = {
        "list": "futures.contractInRoot",
        "fields": FIELDS,
        "root": barchart_root,
        "raw": "1",
    }

    try:
        data = _client.get_json(params)
    except Exception as e:
        log.error("Barchart fetch for %s failed: %s", barchart_root, e)
        return []

    contracts = []
    today = date.today()

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

    if contracts:
        with _cache_lock:
            _curve_cache[cache_key] = contracts
    return contracts
