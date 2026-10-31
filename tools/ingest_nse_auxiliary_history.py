#!/usr/bin/env python3
"""Import separately downloaded official NSE/Nifty Indices history and NSE corporate archives.

The tool never downloads from guessed endpoints. The caller supplies the exact
source URL shown by the official site and the corresponding downloaded file.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

INDEX_HOSTS = {"nseindia.com", "www.nseindia.com", "niftyindices.com", "www.niftyindices.com"}
CORPORATE_HOSTS = {"nseindia.com", "www.nseindia.com"}
INDEX_ALIASES = {
    "date": {"date", "index date", "trading date"},
    "index": {"index", "index name", "indexname"},
    "open": {"open", "open index value"},
    "high": {"high", "high index value"},
    "low": {"low", "low index value"},
    "close": {"close", "closing index value", "close index value"},
}
CORPORATE_FILE = re.compile(r"^(An|Bc|Bm)(\\d{6})\\.(txt|csv)$", re.I)


def _source_ok(url: str, allowed: set[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed:
        raise ValueError("Source URL must be HTTPS on the official NSE/Nifty Indices domain")


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower()).strip()


def parse_index_csv(payload: bytes) -> list[dict]:
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("Index CSV has no header row")
    lookup = {_norm(h): h for h in reader.fieldnames if h}
    selected = {}
    for field, aliases in INDEX_ALIASES.items():
        hit = next((lookup[_norm(a)] for a in aliases if _norm(a) in lookup), None)
        if hit is None:
            raise ValueError(f"Index CSV missing required {field} column")
        selected[field] = hit
    output = []
    seen = set()
    for line, row in enumerate(reader, 2):
        name = (row.get(selected["index"]) or "").strip()
        raw_date = (row.get(selected["date"]) or "").strip()
        if not name or not raw_date:
            raise ValueError(f"Index CSV row {line}: missing index name/date")
        try:
            trade_date = datetime.strptime(raw_date[:10], "%Y-%m-%d").date().isoformat()
        except ValueError:
            try:
                trade_date = datetime.strptime(raw_date, "%d-%b-%Y").date().isoformat()
            except ValueError:
                raise ValueError(f"Index CSV row {line}: unsupported date format {raw_date!r}") from None
        values = {}
        for field in ("open", "high", "low", "close"):
            raw = (row.get(selected[field]) or "").replace(",", "").strip()
            try:
                number = float(raw)
            except ValueError:
                raise ValueError(f"Index CSV row {line}: invalid {field}") from None
            if not (number > 0 and number < 1e10):
                raise ValueError(f"Index CSV row {line}: invalid {field} range")
            values[field] = raw
        if float(values["high"]) < max(float(values["open"]), float(values["low"]), float(values["close"])) or float(values["low"]) > min(float(values["open"]), float(values["high"]), float(values["close"])):
            raise ValueError(f"Index CSV row {line}: inconsistent OHLC range")
        key = (name, trade_date)
        if key in seen:
            raise ValueError(f"Index CSV row {line}: duplicate {name} {trade_date}")
        seen.add(key)
        output.append({"index": name, "date": trade_date, **values, "source": "NSE/Nifty Indices official historical CSV", "marketDataStatus": "EOD"})
    if not output:
        raise ValueError("Index CSV contains no data rows")
    return sorted(output, key=lambda r: (r["index"], r["date"]))


def import_index_csv(path: Path, source_url: str, out: Path, fetched_at=None) -> dict:
    _source_ok(source_url, INDEX_HOSTS)
    payload = path.read_bytes()
    rows = parse_index_csv(payload)
    out.mkdir(parents=True, exist_ok=True)
    by_date = {}
    for row in rows:
        by_date.setdefault(row["date"], []).append(row)
    for day, day_rows in by_date.items():
        target = out / f"{day}.json"
        encoded = json.dumps(day_rows, indent=2) + "\n"
        if target.exists() and target.read_text(encoding="utf-8") != encoded:
            raise ValueError(f"Refusing to overwrite different index history for {day}")
        target.write_text(encoded, encoding="utf-8")
    metadata = {
        "sourceUrl": source_url, "source": "NSE/Nifty Indices official historical CSV",
        "fetchedAt": (fetched_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
        "marketDataStatus": "EOD", "rowCount": len(rows),
        "sha256": hashlib.sha256(payload).hexdigest(), "tradingDates": sorted(by_date),
    }
    (out / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def import_corporate_zip(path: Path, source_url: str, out: Path, fetched_at=None) -> dict:
    _source_ok(source_url, CORPORATE_HOSTS)
    payload = path.read_bytes()
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile:
        raise ValueError("Corporate activity archive is not a valid ZIP") from None
    recognized = []
    for info in archive.infolist():
        if info.is_dir():
            continue
        base = Path(info.filename).name
        match = CORPORATE_FILE.fullmatch(base)
        if not match:
            continue
        kind, date_token, ext = match.groups()
        content = archive.read(info)
        if not content.strip():
            continue
        day = datetime.strptime(date_token, "%d%m%y").date().isoformat()
        kind = kind.lower()
        category = {"an": "announcements", "bc": "corporate_actions", "bm": "board_meetings"}[kind]
        folder = out / category / day
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / base
        if target.exists() and target.read_bytes() != content:
            raise ValueError(f"Refusing to overwrite different corporate history file {target}")
        target.write_bytes(content)
        recognized.append({"file": f"{category}/{day}/{base}", "category": category, "date": day,
                           "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
                           "format": ext.lower(), "status": "RAW_OFFICIAL_SOURCE"})
    if not recognized:
        raise ValueError("ZIP contains no documented NSE announcement, corporate-action or board-meeting files (An/Bc/Bm)")
    metadata = {
        "sourceUrl": source_url, "source": "NSE Market Activity Report archive",
        "fetchedAt": (fetched_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
        "archiveSha256": hashlib.sha256(payload).hexdigest(),
        "files": recognized,
        "note": "Raw source files retained. No event fields are inferred from undocumented delimiters or layouts.",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest-latest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    idx = sub.add_parser("indices")
    idx.add_argument("csv_file", type=Path)
    idx.add_argument("--source-url", required=True)
    idx.add_argument("--output-dir", type=Path, default=Path("data/nse/indices"))
    corp = sub.add_parser("corporate")
    corp.add_argument("zip_file", type=Path)
    corp.add_argument("--source-url", required=True)
    corp.add_argument("--output-dir", type=Path, default=Path("data/nse/corporate"))
    args = parser.parse_args()
    try:
        if args.command == "indices":
            result = import_index_csv(args.csv_file, args.source_url, args.output_dir)
        else:
            result = import_corporate_zip(args.zip_file, args.source_url, args.output_dir)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: auxiliary NSE ingestion failed closed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
