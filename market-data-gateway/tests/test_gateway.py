from fastapi.testclient import TestClient
import app as gateway

client = TestClient(gateway.app)

def test_health_explicitly_does_not_claim_verified_live_data():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["live_data_verified"] is False

def test_invalid_symbol_is_rejected_before_provider_call(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("provider should not be called for invalid symbol")
    monkeypatch.setattr(gateway, "_nse", fail_if_called)
    response = client.get("/v1/quote/RELIANCE%20OR%201%3D1")
    assert response.status_code == 400

def test_history_rejects_reversed_date_range(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("provider should not be called for invalid range")
    monkeypatch.setattr(gateway, "_nse", fail_if_called)
    response = client.get("/v1/history/RELIANCE?from=25-10-2026&to=01-10-2026")
    assert response.status_code == 400

def test_quote_normalizes_52_week_range_and_timestamp(monkeypatch):
    monkeypatch.setattr(gateway, "_nse", lambda path, params: {
        "info": {"companyName": "Reliance Industries"},
        "securityInfo": {"isin": "INE002A01018"},
        "priceInfo": {
            "lastPrice": 1400.0, "previousClose": 1390.0, "open": 1395.0,
            "pChange": 0.72, "lastUpdateTime": "25-Oct-2026 13:10:00",
            "intraDayHighLow": {"max": 1410.0, "min": 1380.0},
            "weekHighLow": {"max": 1600.0, "min": 1111.0}
        }
    })
    body = client.get("/v1/quote/RELIANCE").json()
    assert body["symbol"] == "RELIANCE"
    assert body["last_price"] == 1400.0
    assert body["year_high"] == 1600.0
    assert body["year_low"] == 1111.0
    assert body["live_data_verified"] is False


def test_indices_use_exchange_source_timestamp_and_disclose_unsupported_markets(monkeypatch):
    monkeypatch.setattr(gateway, "_nse", lambda path, params=None: {"data": [
        {"index": "NIFTY 50", "last": "25000", "percentChange": "0.5", "time": "25-Oct-2026 15:30:00"},
        {"index": "NIFTY BANK", "last": "56000", "percentChange": "-0.2", "time": "25-Oct-2026 15:30:00"},
    ]})
    body = client.get("/v1/indices").json()["data"]
    assert body["asOf"] == "2026-10-25T15:30:00+00:00"
    assert body["rows"][0]["sourceTimestamp"] == body["asOf"]
    assert body["marketDataStatus"] == "EOD"
    assert "SENSEX" in body["unsupportedIndices"]
    assert "GOLD FUTURES (GLOBAL)" in body["unsupportedIndices"]


def test_indices_reject_fetch_time_substitution_when_source_timestamp_missing(monkeypatch):
    monkeypatch.setattr(gateway, "_nse", lambda path, params=None: {"data": [
        {"index": "NIFTY 50", "last": "25000", "percentChange": "0.5"}
    ]})
    response = client.get("/v1/indices")
    assert response.status_code == 503
    assert "fetch time is not substituted" in response.json()["detail"]
