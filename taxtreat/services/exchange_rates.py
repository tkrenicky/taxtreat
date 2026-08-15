from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CNB_API_URL = "https://api.cnb.cz/cnbapi/exrates/daily"
CNB_PUBLIC_URL = (
    "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/"
    "kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/index.html"
)


class CnbRateUnavailableError(RuntimeError):
    pass


def _public_url(rate_date: date) -> str:
    return f"{CNB_PUBLIC_URL}?{urlencode({'date': rate_date.strftime('%d.%m.%Y')})}"


def fetch_cnb_exchange_rate(
    currency: str,
    rate_date: date,
    *,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    """Return the CNB fixing as CZK per one unit of foreign currency."""

    code = currency.upper()
    if code == "CZK":
        return {
            "source": "CNB",
            "currency": "CZK",
            "czk_per_unit": "1",
            "effective_date": rate_date.isoformat(),
            "published_for": rate_date.isoformat(),
            "source_url": _public_url(rate_date),
        }

    url = f"{CNB_API_URL}?{urlencode({'date': rate_date.isoformat(), 'lang': 'CZ'})}"
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "TaxTreat/0.2"},
    )
    try:
        with opener(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise CnbRateUnavailableError("CNB exchange-rate service is unavailable.") from exc

    row = next(
        (
            item
            for item in payload.get("rates", [])
            if str(item.get("currencyCode", "")).upper() == code
        ),
        None,
    )
    if row is None:
        raise CnbRateUnavailableError(f"CNB does not publish a rate for {code}.")

    try:
        amount = Decimal(str(row["amount"]))
        published_rate = Decimal(str(row["rate"]))
        per_unit = published_rate / amount
    except (InvalidOperation, KeyError, ZeroDivisionError) as exc:
        raise CnbRateUnavailableError("CNB returned an invalid exchange rate.") from exc

    return {
        "source": "CNB",
        "currency": code,
        "czk_per_unit": format(per_unit, "f"),
        # The rate is applied to the requested decisive date. On a non-working
        # day the API can identify the preceding published fixing separately.
        "effective_date": rate_date.isoformat(),
        "published_for": str(row.get("validFor") or rate_date.isoformat()),
        "source_url": _public_url(rate_date),
        "quoted_amount": int(amount),
        "published_rate": format(published_rate, "f"),
    }
