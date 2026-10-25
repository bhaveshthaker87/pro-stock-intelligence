from __future__ import annotations
import os, re, time
from datetime import datetime, timezone
from typing import Any
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

NSE_HOME = "https://www.nseindia.com"
NSE_API = NSE_HOME + "/api"
SYMBOL_RE = re.compile(r"^[A-Z0-9&._-]{1,30}$")
DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}$")
app = FastAPI(title="Pro Stock Intelligence NSE Gateway", version="0.1.0")
origins = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "https://appassets.androidplatform.net").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET"], allow_headers=["*"])
_session = requests.Session()
_session.headers.update({"User-Agent": os.getenv("NSE_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36"), "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9", "Referer": NSE_HOME + "/"})
_last_bootstrap = 0.0

def _bootstrap() -> None:
    global _last_bootstrap
    if time.monotonic() - _last_bootstrap < 240 and _session.cookies:
        return
    response = _session.get(NSE_HOME, timeout=12)
    response.raise_for_status()
    _last_bootstrap = time.monotonic()

def _nse(path: str, params: dict[str, str] | None = None) -> Any:
    global _last_bootstrap
    try:
        _bootstrap()
        response = _session.get(NSE_API + path, params=params, timeout=15)
        if response.status_code in (401, 403, 429):
            _last_bootstrap = 0.0
            raise HTTPException(status_code=503, detail="NSE temporarily blocked or rate-limited this unofficial endpoint; retry later.")
        response.raise_for_status()
        return response.json()
    except HTTPException:
        raise
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"NSE provider unavailable: {type(exc).__name__}") from exc

def _symbol(value: str) -> str:
    value = value.strip().upper()
    if not SYMBOL_RE.fullmatch(value):
        raise HTTPException(status_code=400, detail="Invalid NSE equity symbol.")
    return value

def _date(value: str) -> str:
    if not DATE_RE.fullmatch(value):
        raise HTTPException(status_code=400, detail="Dates must use DD-MM-YYYY.")
    try: datetime.strptime(value, "%d-%m-%Y")
    except ValueError as exc: raise HTTPException(status_code=400, detail="Invalid calendar date.") from exc
    return value

@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "pro-stock-nse-gateway", "provider": "NSE unofficial public web endpoints", "live_data_verified": False, "checked_at": datetime.now(timezone.utc).isoformat()}

@app.get("/v1/quote/{symbol}")
def quote(symbol: str) -> dict[str, Any]:
    symbol = _symbol(symbol)
    data = _nse("/quote-equity", {"symbol": symbol})
    price, info, security = data.get("priceInfo") or {}, data.get("info") or {}, data.get("securityInfo") or {}
    intraday, year = price.get("intraDayHighLow") or {}, price.get("weekHighLow") or {}
    return {"ok": True, "provider": "NSE", "provider_type": "unofficial_public_endpoint", "symbol": symbol, "company": info.get("companyName"), "last_price": price.get("lastPrice"), "previous_close": price.get("previousClose"), "open": price.get("open"), "day_high": intraday.get("max"), "day_low": intraday.get("min"), "year_high": year.get("max"), "year_low": year.get("min"), "change_percent": price.get("pChange"), "last_update": price.get("lastUpdateTime"), "isin": security.get("isin"), "fetched_at": datetime.now(timezone.utc).isoformat(), "live_data_verified": False}

@app.get("/v1/history/{symbol}")
def history(symbol: str, start: str = Query(..., alias="from"), end: str = Query(..., alias="to")) -> dict[str, Any]:
    symbol, start, end = _symbol(symbol), _date(start), _date(end)
    if datetime.strptime(start, "%d-%m-%Y") > datetime.strptime(end, "%d-%m-%Y"): raise HTTPException(status_code=400, detail="'from' must be on or before 'to'.")
    data = _nse("/historical/cm/equity", {"symbol": symbol, "series": '["EQ"]', "from": start, "to": end})
    rows = data.get("data", []) if isinstance(data, dict) else []
    return {"ok": True, "provider": "NSE", "symbol": symbol, "candles": rows, "count": len(rows), "fetched_at": datetime.now(timezone.utc).isoformat(), "live_data_verified": False}

def _corporate(path: str, symbol: str, start: str | None, end: str | None) -> dict[str, Any]:
    symbol = _symbol(symbol)
    params = {"index": "equities", "symbol": symbol}
    if start: params["from_date"] = _date(start)
    if end: params["to_date"] = _date(end)
    data = _nse(path, params)
    rows = data if isinstance(data, list) else (data.get("data", []) if isinstance(data, dict) else [])
    return {"ok": True, "provider": "NSE", "symbol": symbol, "items": rows, "count": len(rows), "fetched_at": datetime.now(timezone.utc).isoformat(), "live_data_verified": False}

@app.get("/v1/actions/{symbol}")
def actions(symbol: str, start: str | None = None, end: str | None = None) -> dict[str, Any]: return _corporate("/corporates-corporateActions", symbol, start, end)
@app.get("/v1/announcements/{symbol}")
def announcements(symbol: str, start: str | None = None, end: str | None = None) -> dict[str, Any]: return _corporate("/corporates-announcements", symbol, start, end)
@app.get("/v1/board-meetings/{symbol}")
def board_meetings(symbol: str, start: str | None = None, end: str | None = None) -> dict[str, Any]: return _corporate("/corporates-board-meetings", symbol, start, end)
@app.get("/v1/results/{symbol}")
def results(symbol: str, start: str | None = None, end: str | None = None) -> dict[str, Any]: return _corporate("/corporates-financial-results", symbol, start, end)


# Android V40.81 gateway contract compatibility routes.
def _nse_time(value: str) -> str:
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M", "%d-%m-%Y %H:%M:%S"):
        try:
            parsed = datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
            return parsed.isoformat()
        except (ValueError, AttributeError):
            pass
    raise HTTPException(status_code=502, detail="NSE response did not contain a parseable source timestamp.")

@app.get("/v1/quote")
def android_quote(symbol: str = Query(...)) -> dict[str, Any]:
    symbol = _symbol(symbol)
    raw = _nse("/quote-equity", {"symbol": symbol})
    price, info = raw.get("priceInfo") or {}, raw.get("info") or {}
    value = price.get("lastPrice")
    as_of = _nse_time(price.get("lastUpdateTime", ""))
    if not isinstance(value, (int, float)) or value <= 0:
        raise HTTPException(status_code=502, detail="NSE quote missing a positive last price.")
    return {"ok": True, "data": {"symbol": symbol, "price": value, "currency": "INR", "source": "NSE public website (unofficial endpoint)", "marketDataStatus": "EOD", "asOf": as_of, "company": info.get("companyName"), "dayHigh": (price.get("intraDayHighLow") or {}).get("max"), "dayLow": (price.get("intraDayHighLow") or {}).get("min"), "yearHigh": (price.get("weekHighLow") or {}).get("max"), "yearLow": (price.get("weekHighLow") or {}).get("min"), "live_data_verified": False}}

@app.get("/v1/history")
def android_history(symbol: str = Query(...), range: str = Query("1y")) -> dict[str, Any]:
    symbol = _symbol(symbol)
    from datetime import timedelta
    days = {"1m": 31, "3m": 93, "6m": 186, "1y": 366, "2y": 732, "5y": 1830}.get(range, 366)
    end_dt = datetime.now(timezone.utc).date()
    start_dt = end_dt - timedelta(days=days)
    raw = _nse("/historical/cm/equity", {"symbol": symbol, "series": '["EQ"]', "from": start_dt.strftime("%d-%m-%Y"), "to": end_dt.strftime("%d-%m-%Y")})
    source_rows = raw.get("data", []) if isinstance(raw, dict) else []
    rows = []
    for row in source_rows:
        try:
            date_text = row.get("CH_TIMESTAMP") or row.get("mTIMESTAMP") or row.get("TIMESTAMP")
            if not date_text: continue
            dt = datetime.strptime(str(date_text)[:10], "%d-%b-%Y").replace(tzinfo=timezone.utc)
            o = float(row.get("CH_OPENING_PRICE", row.get("OPEN", 0)))
            h = float(row.get("CH_TRADE_HIGH_PRICE", row.get("HIGH", 0)))
            l = float(row.get("CH_TRADE_LOW_PRICE", row.get("LOW", 0)))
            close = float(row.get("CH_CLOSING_PRICE", row.get("CLOSE", 0)))
            volume = float(row.get("CH_TOT_TRADED_QTY", row.get("VOLUME", 0)))
            if min(o, h, l, close) <= 0 or h < max(o, close, l) or l > min(o, close, h) or volume < 0: continue
            rows.append({"time": dt.isoformat(), "open": o, "high": h, "low": l, "close": close, "volume": volume})
        except (ValueError, TypeError):
            continue
    rows.sort(key=lambda item: item["time"])
    if len(rows) < 2:
        raise HTTPException(status_code=503, detail="NSE historical endpoint returned fewer than two valid daily candles.")
    return {"ok": True, "data": {"symbol": symbol, "source": "NSE public website (unofficial endpoint)", "asOf": datetime.now(timezone.utc).isoformat(), "interval": "1d", "rows": rows, "live_data_verified": False}}
