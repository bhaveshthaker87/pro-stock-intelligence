from __future__ import annotations
import os, re, time
from datetime import datetime, timezone, timedelta
from typing import Any
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

NSE_HOME = "https://www.nseindia.com"
NSE_API = NSE_HOME + "/api"

BHARATSTOCK_BASE = os.getenv("BHARATSTOCK_BASE_URL", "https://bharatstockapi.com").rstrip("/")
BHARATSTOCK_API_KEY = os.getenv("BHARATSTOCK_API_KEY", "").strip()

def _bharatstock_enabled() -> bool:
    return bool(BHARATSTOCK_API_KEY)

def _bharatstock_get(path: str, params: dict[str, Any] | None = None) -> Any:
    if not BHARATSTOCK_API_KEY:
        raise HTTPException(status_code=503, detail="BharatStock API key is not configured on the server; no data returned.")
    try:
        response = requests.get(
            BHARATSTOCK_BASE + path,
            params=params,
            headers={"X-API-Key": BHARATSTOCK_API_KEY, "Accept": "application/json"},
            timeout=15,
        )
        if response.status_code == 401:
            raise HTTPException(status_code=503, detail="BharatStock rejected the server API key; check the BHARATSTOCK_API_KEY secret.")
        if response.status_code == 429:
            raise HTTPException(status_code=503, detail="BharatStock free-tier request limit reached; retry after the quota resets.")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="BharatStock has no record for this symbol or endpoint.")
        response.raise_for_status()
        return response.json()
    except HTTPException:
        raise
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"BharatStock provider unavailable: {type(exc).__name__}") from exc

def _bs_rows(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [row for row in raw if isinstance(row, dict)]
    if isinstance(raw, dict):
        for key in ("data", "rows", "items"):
            value = raw.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        if any(key in raw for key in ("trade_date", "close", "latest_price", "pe_ratio")):
            return [raw]
    return []

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
    return {"ok": True, "service": "pro-stock-nse-gateway", "provider": ("BharatStock EOD API configured" if _bharatstock_enabled() else "NSE unofficial public web endpoints"), "bharatstock_configured": _bharatstock_enabled(), "market_data_mode": "EOD", "live_data_verified": False, "checked_at": datetime.now(timezone.utc).isoformat()}

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
    if _bharatstock_enabled():
        ratios = _bharatstock_get(f"/v1/stocks/{symbol}/ratios")
        value = ratios.get("price")
        as_of_date = ratios.get("as_of_date")
        if not isinstance(value, (int, float)) or value <= 0 or not as_of_date:
            raise HTTPException(status_code=502, detail="BharatStock response missing a valid EOD price or source date.")
        try:
            as_of = datetime.strptime(str(as_of_date)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="BharatStock returned an invalid source date.") from exc
        return {"ok": True, "data": {"symbol": symbol, "price": value, "currency": "INR", "source": "BharatStock EOD API", "marketDataStatus": "EOD", "asOf": as_of, "company": ratios.get("company_name") or ratios.get("company") or symbol, "yearHigh": ratios.get("week_52_high"), "yearLow": ratios.get("week_52_low"), "pe": ratios.get("pe_ratio"), "eps": (stock.get("latest_financials") or {}).get("eps"), "live_data_verified": False}}
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
    days = {"1m": 31, "3m": 93, "6m": 186, "1y": 366, "2y": 732, "5y": 1830}.get(range, 366)
    end_dt = datetime.now(timezone.utc).date()
    start_dt = end_dt - timedelta(days=days)
    if _bharatstock_enabled():
        raw_bs = _bharatstock_get(f"/v1/stocks/{symbol}/prices", {"from": start_dt.isoformat(), "to": end_dt.isoformat(), "page_size": 200})
        source_rows = _bs_rows(raw_bs)
        rows = []
        for row in source_rows:
            try:
                day = datetime.strptime(str(row.get("trade_date", ""))[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                o, h, l, c = (float(row[k]) for k in ("open", "high", "low", "close"))
                volume = float(row.get("volume") or 0)
                if min(o, h, l, c) <= 0 or h < max(o, c, l) or l > min(o, c, h) or volume < 0: continue
                rows.append({"time": day.isoformat(), "open": o, "high": h, "low": l, "close": c, "volume": volume})
            except (ValueError, TypeError, KeyError):
                continue
        rows.sort(key=lambda item: item["time"])
        if len(rows) < 2:
            raise HTTPException(status_code=503, detail="BharatStock returned fewer than two valid daily candles; no synthetic candles were created.")
        return {"ok": True, "data": {"symbol": symbol, "source": "BharatStock EOD API", "asOf": rows[-1]["time"], "interval": "1d", "rows": rows, "live_data_verified": False}}
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


# Android V40.81 corporate-event and index contract routes.
def _as_iso_date(value: Any) -> str:
    text = str(value or "").strip()
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return ""

def _as_iso_time(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            return parsed.isoformat()
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
    now = datetime.now(timezone.utc).isoformat()
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
            announced = _as_iso_time(_first(row, "broadcastDate", "announcementDate", "date", "bm_date", "attchmntFileDate"), now)
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
        rows.append({"symbol": sym, "title": title, "eventType": "DIVIDEND", "date": event_date, "eventDate": event_date, "announcedAt": _as_iso_time(_first(row, "broadcastDate", "announcementDate", "date"), now), "recordDate": _as_iso_date(_first(row, "recordDate")) or "", "amount": _first(row, "dividend", "amount")})
    return {"ok": True, "data": {"source": "NSE public website (unofficial endpoint)", "marketDataStatus": "EOD", "asOf": now, "rows": rows, "live_data_verified": False}}

@app.get("/v1/indices")
def android_indices() -> dict[str, Any]:
    raw = _nse("/allIndices")
    now = datetime.now(timezone.utc).isoformat()
    candidates = _items(raw)
    rows = []
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
        rows.append({"name": name, "value": number, "changePct": change})
    if not rows:
        raise HTTPException(status_code=503, detail="NSE /allIndices returned no parseable index rows; no index values were fabricated.")
    return {"ok": True, "data": {"source": "NSE public website (unofficial endpoint)", "marketDataStatus": "EOD", "asOf": now, "rows": rows, "live_data_verified": False}}