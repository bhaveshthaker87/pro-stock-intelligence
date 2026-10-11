#!/usr/bin/env python3
"""Strict contract validator for normalized, authorized market-data gateway JSON.

This validates shape, timestamps, freshness and OHLCV consistency; it does not
certify licensing or truth of a provider's claims. Provider-specific adapters must
map their documented response into the normalized schemas in PROVIDER_GATEWAY.md.
"""
from __future__ import annotations
import argparse, json, math, sys
from datetime import datetime, timezone
from pathlib import Path

STATUSES = {"REALTIME", "DELAYED", "EOD"}
FRESHNESS_SECONDS = {"REALTIME": 300, "DELAYED": 86400, "EOD": 259200}
EVENT_TYPES = {"RESULTS", "DIVIDEND", "SPLIT", "BONUS", "RIGHTS", "BOARD_MEETING", "OTHER"}

def parse_time(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be an ISO-8601 timestamp with timezone")
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp with timezone") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone offset")
    return dt.astimezone(timezone.utc)

def load(path):
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON payload: {exc}") from exc
    if not isinstance(obj, dict): raise ValueError("Top-level JSON must be an object")
    return obj

def base(payload):
    for k in ("symbol", "source", "asOf"):
        if not isinstance(payload.get(k), str) or not payload[k].strip():
            raise ValueError(f"{k} is required and must be a non-empty string")
    parse_time(payload["asOf"], "asOf")

def validate_quote(payload, now=None):
    base(payload)
    price=payload.get("price")
    if isinstance(price, bool) or not isinstance(price, (int,float)) or not math.isfinite(price) or price <= 0:
        raise ValueError("price must be a finite positive number")
    if not isinstance(payload.get("currency"), str) or not payload["currency"].strip():
        raise ValueError("currency is required")
    status=payload.get("marketDataStatus")
    if status not in STATUSES: raise ValueError("marketDataStatus must be REALTIME, DELAYED or EOD")
    asof=parse_time(payload["asOf"], "asOf")
    now=now or datetime.now(timezone.utc)
    if asof > now.replace(microsecond=0).replace(second=now.second) and (asof-now).total_seconds() > 300:
        raise ValueError("asOf is more than 5 minutes in the future")
    age=(now-asof).total_seconds()
    if age > FRESHNESS_SECONDS[status]:
        raise ValueError(f"quote is stale for declared {status} status ({int(age)} seconds old)")
    if status == "DELAYED" and (not isinstance(payload.get("delayMinutes"), int) or payload["delayMinutes"] <= 0):
        raise ValueError("DELAYED quotes require a positive integer delayMinutes")
    return {"kind":"quote", "symbol":payload["symbol"].upper(), "status":status, "ageSeconds":int(max(0,age))}

def validate_history(payload):
    base(payload)
    rows=payload.get("rows")
    if not isinstance(rows,list) or len(rows)<2: raise ValueError("history.rows must contain at least two bars")
    interval=payload.get("interval")
    if interval not in {"1m","5m","15m","1d","1wk","1mo"}: raise ValueError("unsupported history interval")
    previous=None
    for i,row in enumerate(rows):
        if not isinstance(row,dict): raise ValueError(f"rows[{i}] must be an object")
        dt=parse_time(row.get("time"), f"rows[{i}].time")
        if previous is not None and dt <= previous: raise ValueError("history timestamps must be strictly increasing with no duplicates")
        previous=dt
        vals={k:row.get(k) for k in ("open","high","low","close","volume")}
        for k,v in vals.items():
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v): raise ValueError(f"rows[{i}].{k} must be finite numeric")
        if min(vals[k] for k in ("open","high","low","close")) <= 0: raise ValueError(f"rows[{i}] OHLC values must be positive")
        if vals["high"] < max(vals[k] for k in ("open","low","close")): raise ValueError(f"rows[{i}].high is inconsistent with OHLC")
        if vals["low"] > min(vals[k] for k in ("open","high","close")): raise ValueError(f"rows[{i}].low is inconsistent with OHLC")
        if vals["volume"] < 0: raise ValueError(f"rows[{i}].volume cannot be negative")
    return {"kind":"history", "symbol":payload["symbol"].upper(), "bars":len(rows), "interval":interval}

def validate_events(payload):
    base(payload)
    rows=payload.get("rows")
    if not isinstance(rows,list): raise ValueError("rows must be an array; empty array means unknown/none returned, not verified absence")
    for i,row in enumerate(rows):
        if not isinstance(row,dict): raise ValueError(f"rows[{i}] must be an object")
        if not isinstance(row.get("symbol"),str) or not row["symbol"].strip(): raise ValueError(f"rows[{i}].symbol is required")
        if row.get("eventType") not in EVENT_TYPES: raise ValueError(f"rows[{i}].eventType is unsupported")
        if not isinstance(row.get("title"),str) or not row["title"].strip(): raise ValueError(f"rows[{i}].title is required")
        parse_time(row.get("announcedAt"), f"rows[{i}].announcedAt")
        event_date=row.get("eventDate")
        if not isinstance(event_date,str) or len(event_date)<10:
            raise ValueError(f"rows[{i}].eventDate must be an ISO date or timestamp")
        try: datetime.fromisoformat(event_date[:10])
        except ValueError as exc: raise ValueError(f"rows[{i}].eventDate must begin with YYYY-MM-DD") from exc
    return {"kind":"events", "symbol":payload["symbol"].upper(), "eventsReturned":len(rows), "absenceVerified":False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("kind",choices=["quote","history","events"])
    ap.add_argument("json_file")
    args=ap.parse_args()
    try:
        p=load(args.json_file)
        result={"quote":validate_quote,"history":validate_history,"events":validate_events}[args.kind](p)
        print(json.dumps({"ok":True,"validation":result},sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"ok":False,"error":str(exc)},sort_keys=True),file=sys.stderr)
        return 2
if __name__=="__main__": raise SystemExit(main())
