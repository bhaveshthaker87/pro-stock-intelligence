from __future__ import annotations
import os, re, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
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
    # NSE timestamps are exchange-local wall time. Interpret them in IST first;
    # attaching UTC directly shifts every source timestamp by 5 hours 30 minutes.
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M", "%d-%m-%Y %H:%M:%S"):
        try:
            parsed = datetime.strptime(value.strip(), fmt).replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            return parsed.astimezone(timezone.utc).isoformat()
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
    ist_today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    supported_ranges = {"1d": 7, "1w": 7, "1mo": 31, "3mo": 93, "6mo": 186, "1y": 366, "3y": 1098, "5y": 1830}
    if range == "ytd":
        start_dt = ist_today.replace(month=1, day=1)
    elif range == "all":
        start_dt = datetime(2000, 1, 1).date()
    elif range in supported_ranges:
        start_dt = ist_today - timedelta(days=supported_ranges[range])
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported history range: {range}")
    end_dt = ist_today
    raw = _nse("/historical/cm/equity", {"symbol": symbol, "series": '["EQ"]', "from": start_dt.strftime("%d-%m-%Y"), "to": end_dt.strftime("%d-%m-%Y")})
    source_rows = raw.get("data", []) if isinstance(raw, dict) else []
    rows = []
    for row in source_rows:
        try:
            date_text = row.get("CH_TIMESTAMP") or row.get("mTIMESTAMP") or row.get("TIMESTAMP")
            if not date_text: continue
            dt = datetime.strptime(str(date_text)[:10], "%d-%b-%Y").replace(tzinfo=ZoneInfo("Asia/Kolkata"))
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
    # The 1D selection is one latest daily EOD candle, not intraday history.
    if range == "1d" and rows:
        rows = rows[-1:]
    minimum_rows = 1 if range == "1d" else 2
    if len(rows) < minimum_rows:
        raise HTTPException(status_code=503, detail=f"NSE historical endpoint returned fewer than {minimum_rows} valid daily EOD candle(s) for range {range}.")
    return {"ok": True, "data": {"symbol": symbol, "source": "NSE public website (unofficial endpoint)", "asOf": datetime.now(timezone.utc).isoformat(), "interval": "1d", "rangeRequested": range, "rangeStart": start_dt.isoformat(), "rangeEnd": end_dt.isoformat(), "rows": rows, "live_data_verified": False}}


# Android V40.81 corporate-event and index contract routes.
def _as_iso_date(value: Any) -> str:
    text = str(value or "").strip()
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return ""

def _as_iso_time(value: Any, fallback: str | None = None) -> str | None:
    text = str(value or "").strip()
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.strptime(text, fmt).replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            return parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return fallback

def _items(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, dict):
        for key in ("data", "rows", "items", "corporateActions", "announcements"):
            val = raw.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
    return []

def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None

def _event_rows(symbol: str, event_type: str) -> list[dict[str, Any]]:
    paths = [
        ("DIVIDEND", "/corporates-corporateActions"),
        ("SPLIT", "/corporates-corporateActions"),
        ("BONUS", "/corporates-corporateActions"),
        ("RIGHTS", "/corporates-corporateActions"),
        ("BOARD_MEETING", "/corporates-board-meetings"),
        ("RESULTS", "/corporates-financial-results"),
        ("OTHER", "/corporates-announcements"),
    ]
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for kind, path in paths:
        if event_type not in ("ALL", kind):
            continue
        params = {"index": "equities"}
        if symbol:
            params["symbol"] = symbol
        raw = _nse(path, params)
        for row in _items(raw):
            row_symbol = str(_first(row, "symbol", "symbolName", "sm_symbol", "ticker") or symbol).strip().upper()
            if not row_symbol or (symbol and row_symbol != symbol):
                continue
            try:
                row_symbol = _symbol(row_symbol)
            except HTTPException:
                continue
            title = str(_first(row, "subject", "purpose", "desc", "description", "bm_desc", "meetingPurpose", "companyName") or "").strip()
            date = _as_iso_date(_first(row, "exDate", "exDate1", "recordDate", "meetingDate", "bm_date", "broadcastDate", "date", "resultDate", "attchmntFileDate"))
            if not title or not date:
                continue
            normalized_kind = kind
            lower = title.lower()
            if kind in ("DIVIDEND", "SPLIT", "BONUS", "RIGHTS"):
                if "dividend" in lower: normalized_kind = "DIVIDEND"
                elif "split" in lower: normalized_kind = "SPLIT"
                elif "bonus" in lower: normalized_kind = "BONUS"
                elif "right" in lower: normalized_kind = "RIGHTS"
                else: continue
            if event_type not in ("ALL", normalized_kind):
                continue
            announced = _as_iso_time(_first(row, "broadcastDate", "announcementDate", "attchmntFileDate"))
            key = (row_symbol, normalized_kind, date, title)
            if key in seen: continue
            seen.add(key)
            result.append({
                "symbol": row_symbol,
                "company": str(_first(row, "companyName", "company", "sm_name") or row_symbol),
                "eventType": normalized_kind,
                "title": title,
                "eventDate": date,
                "announcedAt": announced,
                "recordDate": _as_iso_date(_first(row, "recordDate")) or "",
                "dividend": _first(row, "dividend"),
                "ratio": _first(row, "ratio"),
            })
    result.sort(key=lambda x: (x["eventDate"], x["symbol"]))
    return result

@app.get("/v1/events")
def android_events(eventType: str = Query("ALL"), symbol: str = Query("")) -> dict[str, Any]:
    kind = eventType.strip().upper()
    allowed = {"ALL", "RESULTS", "DIVIDEND", "SPLIT", "BONUS", "RIGHTS", "BOARD_MEETING", "OTHER"}
    if kind not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported eventType.")
    sym = _symbol(symbol) if symbol.strip() else ""
    rows = _event_rows(sym, kind)
    return {"ok": True, "data": {"source": "NSE public website (unofficial endpoint)", "marketDataStatus": "EOD", "asOf": datetime.now(timezone.utc).isoformat(), "rows": rows, "live_data_verified": False}}

@app.get("/v1/dividends")
def android_dividends() -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    raw = _nse("/corporates-corporateActions", {"index": "equities"})
    rows = []
    for row in _items(raw):
        title = str(_first(row, "subject", "purpose", "desc", "description") or "").strip()
        sym = str(_first(row, "symbol", "symbolName", "sm_symbol", "ticker") or "").strip().upper()
        if "dividend" not in title.lower() or not sym:
            continue
        try:
            sym = _symbol(sym)
        except HTTPException:
            continue
        event_date = _as_iso_date(_first(row, "exDate", "exDate1", "recordDate", "date"))
        if not event_date:
            continue
        rows.append({"symbol": sym, "title": title, "eventType": "DIVIDEND", "date": event_date, "eventDate": event_date, "announcedAt": _as_iso_time(_first(row, "broadcastDate", "announcementDate")), "recordDate": _as_iso_date(_first(row, "recordDate")) or "", "amount": _first(row, "dividend", "amount")})
    return {"ok": True, "data": {"source": "NSE public website (unofficial endpoint)", "marketDataStatus": "EOD", "asOf": now, "rows": rows, "live_data_verified": False}}

@app.get("/v1/indices")
def android_indices() -> dict[str, Any]:
    raw = _nse("/allIndices")
    candidates = _items(raw)
    rows = []
    source_times: list[datetime] = []
    aliases = {
        "NIFTY 50": ("NIFTY 50", "NIFTY 50"),
        "NIFTY BANK": ("NIFTY BANK", "NIFTY BANK"),
        "NIFTY IT": ("NIFTY IT", "NIFTY IT"),
        "NIFTY NEXT 50": ("NIFTY NEXT 50", "NIFTY NEXT 50"),
        "NIFTY MIDCAP 100": ("NIFTY MIDCAP 100", "NIFTY MIDCAP 100"),
        "NIFTY SMALLCAP 100": ("NIFTY SMALLCAP 100", "NIFTY SMALLCAP 100"),
    }
    for row in candidates:
        name = str(_first(row, "index", "indexName", "name") or "").strip()
        if not name:
            continue
        value = _first(row, "last", "lastPrice", "indexValue", "value")
        pct = _first(row, "percentChange", "pChange", "changePct")
        try:
            number = float(str(value).replace(",", ""))
            change = float(str(pct).replace(",", ""))
        except (TypeError, ValueError):
            continue
        if number <= 0:
            continue
        stamp_text = str(_first(row, "time", "lastUpdateTime", "timestamp", "date") or "").strip()
        if not stamp_text:
            continue
        try:
            stamp_iso = _nse_time(stamp_text)
            stamp_dt = datetime.fromisoformat(stamp_iso)
        except (HTTPException, ValueError):
            continue
        source_times.append(stamp_dt)
        rows.append({"name": name, "value": number, "changePct": change, "sourceTimestamp": stamp_iso})
    if not rows or not source_times:
        raise HTTPException(status_code=503, detail="NSE /allIndices returned no rows with a parseable exchange source timestamp; fetch time is not substituted.")
    # Use the actual source timestamp from the returned NSE index rows, never request/response time.
    as_of = max(source_times).isoformat()
    return {"ok": True, "data": {"source": "NSE public website (unofficial endpoint)", "marketDataStatus": "EOD", "asOf": as_of, "rows": rows, "live_data_verified": False, "unsupportedIndices": ["SENSEX", "GOLD FUTURES (GLOBAL)", "SILVER FUTURES (GLOBAL)", "BRENT CRUDE (GLOBAL)"]}}
