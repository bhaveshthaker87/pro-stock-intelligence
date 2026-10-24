#!/usr/bin/env python3
"""Strict validators for normalized, authorized market-data gateway JSON.

Validates payload shape, symbol identity, timestamps, freshness and OHLCV consistency.
It does not certify licensing or the truth of a provider's claims.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
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
    if not isinstance(obj, dict):
        raise ValueError("Top-level JSON must be an object")
    return obj


def base(payload, require_symbol=True):
    keys = (("symbol",) if require_symbol else ()) + ("source", "asOf")
    for key in keys:
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise ValueError(f"{key} is required and must be a non-empty string")
    return parse_time(payload["asOf"], "asOf")


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_status_freshness(payload, now=None):
    status = payload.get("marketDataStatus")
    if status not in STATUSES:
        raise ValueError("marketDataStatus must be REALTIME, DELAYED or EOD")
    asof = parse_time(payload["asOf"], "asOf")
    now = now or datetime.now(timezone.utc)
    age = (now - asof).total_seconds()
    if age < -300:
        raise ValueError("asOf is more than 5 minutes in the future")
    if age > FRESHNESS_SECONDS[status]:
        raise ValueError(f"payload is stale for declared {status} status ({int(age)} seconds old)")
    if status == "DELAYED" and (
        not isinstance(payload.get("delayMinutes"), int)
        or isinstance(payload.get("delayMinutes"), bool)
        or payload["delayMinutes"] <= 0
    ):
        raise ValueError("DELAYED payloads require a positive integer delayMinutes")
    return status, int(max(0, age))


def validate_quote(payload, now=None, expected_symbol=None):
    base(payload)
    symbol = payload["symbol"].strip().upper()
    if expected_symbol and symbol != expected_symbol.strip().upper():
        raise ValueError(f"symbol mismatch: requested {expected_symbol.strip().upper()}, received {symbol}")
    price = payload.get("price")
    if not finite_number(price) or price <= 0:
        raise ValueError("price must be a finite positive number")
    if not isinstance(payload.get("currency"), str) or not payload["currency"].strip():
        raise ValueError("currency is required")
    status, age = validate_status_freshness(payload, now)
    return {"kind": "quote", "symbol": symbol, "status": status, "ageSeconds": age}


def validate_history(payload, expected_symbol=None, now=None):
    asof = base(payload)
    now = now or datetime.now(timezone.utc)
    age = (now - asof).total_seconds()
    if age < -300:
        raise ValueError("history snapshot timestamp is more than 5 minutes in the future")
    if age > 86400:
        raise ValueError(f"history snapshot is stale ({int(age)} seconds old)")
    symbol = payload["symbol"].strip().upper()
    if expected_symbol and symbol != expected_symbol.strip().upper():
        raise ValueError(f"symbol mismatch: requested {expected_symbol.strip().upper()}, received {symbol}")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError("history.rows must contain at least two bars")
    interval = payload.get("interval")
    if interval not in {"1m", "5m", "15m", "1d", "1wk", "1mo"}:
        raise ValueError("unsupported history interval")
    previous = None
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"rows[{i}] must be an object")
        dt = parse_time(row.get("time"), f"rows[{i}].time")
        if dt > now.replace(microsecond=0) and (dt - now).total_seconds() > 300:
            raise ValueError(f"rows[{i}].time is in the future")
        if previous is not None and dt <= previous:
            raise ValueError("history timestamps must be strictly increasing with no duplicates")
        previous = dt
        vals = {key: row.get(key) for key in ("open", "high", "low", "close", "volume")}
        for key, value in vals.items():
            if not finite_number(value):
                raise ValueError(f"rows[{i}].{key} must be finite numeric")
        if min(vals[key] for key in ("open", "high", "low", "close")) <= 0:
            raise ValueError(f"rows[{i}] OHLC values must be positive")
        if vals["high"] < max(vals[key] for key in ("open", "low", "close")):
            raise ValueError(f"rows[{i}].high is inconsistent with OHLC")
        if vals["low"] > min(vals[key] for key in ("open", "high", "close")):
            raise ValueError(f"rows[{i}].low is inconsistent with OHLC")
        if vals["volume"] < 0:
            raise ValueError(f"rows[{i}].volume cannot be negative")
    return {"kind": "history", "symbol": symbol, "bars": len(rows), "interval": interval}


def validate_events(payload, now=None):
    asof = base(payload)
    now = now or datetime.now(timezone.utc)
    age = (now - asof).total_seconds()
    if age < -300:
        raise ValueError("events snapshot timestamp is more than 5 minutes in the future")
    if age > 86400:
        raise ValueError(f"events snapshot is stale ({int(age)} seconds old)")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be an array; empty array means unknown/none returned, not verified absence")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"rows[{i}] must be an object")
        if not isinstance(row.get("symbol"), str) or not row["symbol"].strip():
            raise ValueError(f"rows[{i}].symbol is required")
        if row.get("eventType") not in EVENT_TYPES:
            raise ValueError(f"rows[{i}].eventType is unsupported")
        if not isinstance(row.get("title"), str) or not row["title"].strip():
            raise ValueError(f"rows[{i}].title is required")
        parse_time(row.get("announcedAt"), f"rows[{i}].announcedAt")
        event_date = row.get("eventDate")
        if not isinstance(event_date, str) or len(event_date) < 10:
            raise ValueError(f"rows[{i}].eventDate must be an ISO date or timestamp")
        try:
            datetime.fromisoformat(event_date[:10])
        except ValueError as exc:
            raise ValueError(f"rows[{i}].eventDate must begin with YYYY-MM-DD") from exc
    return {"kind": "events", "symbol": payload["symbol"].upper(), "eventsReturned": len(rows), "absenceVerified": False}


def validate_indices(payload, now=None):
    base(payload, require_symbol=False)
    status, age = validate_status_freshness(payload, now)
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("indices.rows must be a non-empty array; empty data cannot be treated as a valid index feed")
    seen = set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"rows[{i}] must be an object")
        name = row.get("symbol") or row.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"rows[{i}] requires symbol or name")
        key = name.strip().upper()
        if key in seen:
            raise ValueError(f"duplicate index row: {key}")
        seen.add(key)
        value = row.get("value")
        if not finite_number(value) or value <= 0:
            raise ValueError(f"rows[{i}].value must be a finite positive number")
        for key in ("previousClose", "change", "changePct"):
            if key in row and row[key] is not None and not finite_number(row[key]):
                raise ValueError(f"rows[{i}].{key} must be finite numeric when present")
    return {"kind": "indices", "status": status, "ageSeconds": age, "indicesReturned": len(rows)}


def validate_dividends(payload):
    base(payload, require_symbol=False)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("dividends.rows must be an array; empty rows do not verify absence of dividends")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"rows[{i}] must be an object")
        if not isinstance(row.get("symbol"), str) or not row["symbol"].strip():
            raise ValueError(f"rows[{i}].symbol is required")
        date_value = row.get("exDate") or row.get("eventDate") or row.get("recordDate")
        if not isinstance(date_value, str) or len(date_value) < 10:
            raise ValueError(f"rows[{i}] requires exDate, eventDate, or recordDate")
        try:
            datetime.fromisoformat(date_value[:10])
        except ValueError as exc:
            raise ValueError(f"rows[{i}] dividend date must begin with YYYY-MM-DD") from exc
        amount = row.get("amount")
        if amount is not None and (not finite_number(amount) or amount <= 0):
            raise ValueError(f"rows[{i}].amount must be a positive finite number when present")
        if amount is not None and (not isinstance(row.get("currency"), str) or not row["currency"].strip()):
            raise ValueError(f"rows[{i}].currency is required when amount is present")
    return {"kind": "dividends", "status": status, "ageSeconds": age, "dividendsReturned": len(rows), "absenceVerified": False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("kind", choices=["quote", "history", "events", "indices", "dividends"])
    ap.add_argument("json_file")
    ap.add_argument("--expected-symbol", help="Reject a quote/history payload for a different requested symbol")
    args = ap.parse_args()
    try:
        payload = load(args.json_file)
        validators = {
            "quote": lambda p: validate_quote(p, expected_symbol=args.expected_symbol),
            "history": lambda p: validate_history(p, expected_symbol=args.expected_symbol),
            "events": validate_events,
            "indices": validate_indices,
            "dividends": validate_dividends,
        }
        result = validators[args.kind](payload)
        print(json.dumps({"ok": True, "validation": result}, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
