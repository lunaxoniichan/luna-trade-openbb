from datetime import date
import math

import pytest

from openbb_yfinance.models.currency_historical import (
    YFinanceCurrencyHistoricalFetcher,
    YFinanceCurrencyHistoricalQueryParams,
)


def test_currency_historical_endpoint_returns_clear_422_for_nonfinite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Endpoint-level check:
    - we mock the yfinance fetcher to return NaN
    - ensure OpenBB returns 422 with our descriptive message (not a generic JSON error)
    """
    from fastapi.testclient import TestClient

    from openbb_core.api.rest_api import app as openbb_app

    def mock_extract_data(query, credentials, **kwargs):  # type: ignore[no-untyped-def]
        return [
            {
                "date": date(2026, 3, 26),
                "open": 150.0,
                "high": 151.0,
                "low": 149.0,
                "close": float("nan"),
                "volume": None,
                "vwap": None,
            }
        ]

    monkeypatch.setattr(
        YFinanceCurrencyHistoricalFetcher,
        "extract_data",
        staticmethod(mock_extract_data),
    )

    client = TestClient(openbb_app)
    resp = client.get(
        "/api/v1/currency/price/historical",
        params={
            "provider": "yfinance",
            "symbol": "USDJPY",
            "start_date": "2026-03-19",
            "end_date": "2026-03-26",
        },
    )

    assert resp.status_code == 422
    body = resp.json()
    # The old behavior was a generic "Out of range float values are not JSON compliant".
    assert "Out of range float values are not JSON compliant" not in str(body)
    assert "Non-finite float value encountered" in str(body)


def _make_query() -> YFinanceCurrencyHistoricalQueryParams:
    # Symbol should look like yfinance expects (e.g. USDJPY=X).
    return YFinanceCurrencyHistoricalQueryParams(
        symbol="USDJPY=X",
        start_date=date(2026, 3, 19),
        end_date=date(2026, 3, 26),
    )


def test_currency_historical_nonfinite_close_raises() -> None:
    fetcher = YFinanceCurrencyHistoricalFetcher()
    query = _make_query()

    record = {
        "date": date(2026, 3, 26),
        "open": 150.0,
        "high": 151.0,
        "low": 149.0,
        "close": float("nan"),
        "volume": None,
        "vwap": None,
    }

    with pytest.raises(ValueError) as exc:
        fetcher.transform_data(query=query, data=[record])

    msg = str(exc.value)
    assert "Non-finite float value encountered" in msg
    assert "field=close" in msg
    assert "symbol=USDJPY=X" in msg


def test_currency_historical_nonfinite_open_raises() -> None:
    fetcher = YFinanceCurrencyHistoricalFetcher()
    query = _make_query()

    record = {
        "date": date(2026, 3, 26),
        "open": math.inf,
        "high": 151.0,
        "low": 149.0,
        "close": 150.0,
        "volume": None,
        "vwap": None,
    }

    with pytest.raises(ValueError) as exc:
        fetcher.transform_data(query=query, data=[record])

    msg = str(exc.value)
    assert "Non-finite float value encountered" in msg
    assert "field=open" in msg
    assert "symbol=USDJPY=X" in msg

