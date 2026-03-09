from datetime import date
from dateutil.relativedelta import relativedelta

from app.config import CommodityConfig, MONTH_CODES


def build_ticker_chain(config: CommodityConfig, from_date: date | None = None) -> list[dict]:
    """Generate futures ticker chain for a commodity starting from a given date.

    Returns a list of dicts with ticker, approximate expiry date, and label
    for each contract month in the chain.
    """
    if not config.root_symbol:
        return []

    start = from_date or date.today()
    # Start from the current month
    start = start.replace(day=1)
    contracts = []

    for i in range(config.chain_depth):
        target = start + relativedelta(months=i)
        month_code = MONTH_CODES[target.month]
        year_suffix = str(target.year)[-2:]
        ticker = f"{config.root_symbol}{month_code}{year_suffix}.{config.exchange}"
        contracts.append({
            "ticker": ticker,
            "expiry_approx": date(target.year, target.month, 15).isoformat(),
            "label": target.strftime("%b %Y"),
        })

    return contracts
