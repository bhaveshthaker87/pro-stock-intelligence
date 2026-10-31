#!/usr/bin/env python3
"""Convert an official NSE CM UDiFF bhavcopy ZIP into a normalized EOD CSV.

This tool intentionally handles only NSE cash-market EQ rows. It never fetches
quotes or labels an EOD close as live. Source trading date is retained per row.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import zipfile
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

OUTPUT_FIELDS = (
    "symbol", "date", "open", "high", "low", "close", "volume",
    "source", "marketDataStatus",
)
REQUIRED_COLUMNS = {
    "TradDt", "TckrSymb", "SctySrs", "OpnPric", "HghPric",
    "LwPric", "ClsPric", "TtlTradgVol",
}
SOURCE = "NSE CM-UDiFF Common Bhavcopy Final"


class BhavcopyError(ValueError):
    """Raised when the supplied file is not a valid NSE cash UDiFF bhavcopy."""


def _number(value: str, field: str, row_number: int) -> Decimal:
    try:
        number = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, AttributeError):
        raise BhavcopyError(f"row {row_number}: invalid {field}") from None
    if not number.is_finite() or number < 0:
        raise BhavcopyError(f"row {row_number}: invalid {field}")
    return number


def parse_bhavcopy_zip(payload: bytes) -> list[dict[str, str]]:
    """Parse a UDiFF ZIP into validated, sorted EQ daily bars."""
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            csv_names = [n for n in archive.namelist() if n.lower().endswith(".csv") and not n.startswith("__MACOSX/")]
            if len(csv_names) != 1:
                raise BhavcopyError("ZIP must contain exactly one CSV data file")
            raw = archive.read(csv_names[0]).decode("utf-8-sig")
    except (zipfile.BadZipFile, UnicodeDecodeError, OSError) as exc:
        raise BhavcopyError(f"cannot read NSE UDiFF ZIP: {type(exc).__name__}") from exc

    reader = csv.DictReader(io.StringIO(raw))
    headers = {str(h or "").strip() for h in (reader.fieldnames or [])}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise BhavcopyError("missing UDiFF columns: " + ", ".join(sorted(missing)))

    rows: dict[tuple[str, str], dict[str, str]] = {}
    for row_number, raw_row in enumerate(reader, start=2):
        row = {str(k).strip(): (v or "").strip() for k, v in raw_row.items() if k is not None}
        if row.get("SctySrs", "").upper() != "EQ":
            continue
        symbol = row.get("TckrSymb", "").upper()
        if not re.fullmatch(r"[A-Z0-9&._-]{1,30}", symbol):
            raise BhavcopyError(f"row {row_number}: invalid EQ symbol")
        try:
            trade_date = date.fromisoformat(row["TradDt"][:10]).isoformat()
        except (KeyError, ValueError):
            raise BhavcopyError(f"row {row_number}: invalid TradDt") from None

        opening = _number(row.get("OpnPric", ""), "OpnPric", row_number)
        high = _number(row.get("HghPric", ""), "HghPric", row_number)
        low = _number(row.get("LwPric", ""), "LwPric", row_number)
        close = _number(row.get("ClsPric", ""), "ClsPric", row_number)
        volume = _number(row.get("TtlTradgVol", ""), "TtlTradgVol", row_number)
        if min(opening, high, low, close) <= 0:
            raise BhavcopyError(f"row {row_number}: OHLC prices must be positive")
        if high < max(opening, close, low) or low > min(opening, close, high):
            raise BhavcopyError(f"row {row_number}: inconsistent OHLC range")
        key = (symbol, trade_date)
        if key in rows:
            raise BhavcopyError(f"duplicate EQ row for {symbol} on {trade_date}")
        rows[key] = {
            "symbol": symbol, "date": trade_date,
            "open": str(opening), "high": str(high), "low": str(low),
            "close": str(close), "volume": str(volume),
            "source": SOURCE, "marketDataStatus": "EOD",
        }
    if not rows:
        raise BhavcopyError("no valid EQ rows found in NSE cash-market file")
    return [rows[key] for key in sorted(rows, key=lambda x: (x[1], x[0]))]


def convert(input_path: Path, output_path: Path) -> int:
    rows = parse_bhavcopy_zip(input_path.read_bytes())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    dates = sorted({row["date"] for row in rows})
    print(f"Converted {len(rows)} NSE EQ bars for {', '.join(dates)}; status=EOD; source={SOURCE}")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_zip", type=Path, help="Official NSE CM-UDiFF bhavcopy ZIP")
    parser.add_argument("-o", "--output", type=Path, default=Path("nse_eod_import.csv"))
    args = parser.parse_args()
    try:
        convert(args.input_zip, args.output)
    except (OSError, BhavcopyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
