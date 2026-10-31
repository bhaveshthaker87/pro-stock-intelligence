#!/usr/bin/env python3
"""Fetch the official NSE CM-UDiFF EOD report and persist validated daily EQ history.

Discovery is intentionally fail-closed: only an HTTPS link exposed by NSE's
official All Reports page and matching the documented UDiFF filename is used.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from convert_nse_udiff_bhavcopy import OUTPUT_FIELDS, parse_bhavcopy_zip

REPORTS_URL = "https://www.nseindia.com/all-reports"
REPORT_RE = re.compile(r"BhavCopy_NSE_CM_0_0_0_(\d{8})_F_0000\.csv\.zip", re.I)
USER_AGENT = "Mozilla/5.0 (compatible; ProStockIntelligence-EOD/1.0)"


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None
            self._text = []


def discover_report_url(html: str, base_url: str = REPORTS_URL) -> str:
    parser = LinkParser()
    parser.feed(html)
    candidates = []
    for href, label in parser.links:
        if not href:
            continue
        match = REPORT_RE.search(href) or REPORT_RE.search(label)
        if not match:
            continue
        url = urljoin(base_url, href)
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in {"nseindia.com", "www.nseindia.com"}:
            continue
        candidates.append((match.group(1), url))
    if not candidates:
        raise ValueError("NSE All Reports page did not expose a matching official CM-UDiFF ZIP link")
    # Pick the latest trading date advertised by the official page.
    return sorted(candidates, key=lambda item: item[0])[-1][1]


def _get(url: str, timeout: int = 30) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/zip,application/octet-stream,*/*",
        "Referer": REPORTS_URL,
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Unexpected HTTP status {response.status} for NSE source")
        final = urlparse(response.geturl())
        if final.scheme != "https" or final.hostname not in {"nseindia.com", "www.nseindia.com"}:
            raise RuntimeError("NSE download redirected outside the official NSE HTTPS domain")
        return response.read()


def ingest(output_root: Path, html: str | None = None, zip_payload: bytes | None = None,
           fetched_at: datetime | None = None) -> dict:
    page = html if html is not None else _get(REPORTS_URL).decode("utf-8", errors="replace")
    report_url = discover_report_url(page)
    match = REPORT_RE.search(report_url)
    if not match:
        raise ValueError("Discovered report URL has no valid NSE trading date")
    trading_date = datetime.strptime(match.group(1), "%Y%m%d").date()
    payload = zip_payload if zip_payload is not None else _get(report_url)
    rows = parse_bhavcopy_zip(payload)
    row_dates = {row["date"] for row in rows}
    if row_dates != {trading_date.isoformat()}:
        raise ValueError(f"Report date mismatch: filename={trading_date}, rows={sorted(row_dates)}")

    output_root.mkdir(parents=True, exist_ok=True)
    daily_path = output_root / f"{trading_date.isoformat()}.csv"
    import io
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    csv_text = stream.getvalue()
    if daily_path.exists() and daily_path.read_text(encoding="utf-8") != csv_text:
        raise ValueError(f"Refusing to overwrite different history for {trading_date}")
    daily_path.write_text(csv_text, encoding="utf-8", newline="")
    timestamp = (fetched_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    metadata = {
        "tradingDate": trading_date.isoformat(),
        "fetchedAt": timestamp,
        "source": "NSE CM-UDiFF Common Bhavcopy Final",
        "sourceUrl": report_url,
        "marketDataStatus": "EOD",
        "rowCount": len(rows),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "file": daily_path.name,
    }
    meta_path = output_root / f"{trading_date.isoformat()}.json"
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    entries = []
    for path in sorted(output_root.glob("????-??-??.json")):
        try:
            entries.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            raise ValueError(f"Invalid history metadata: {path.name}")
    manifest = {
        "source": "NSE CM-UDiFF Common Bhavcopy Final",
        "marketDataStatus": "EOD",
        "updatedAt": timestamp,
        "tradingDates": entries,
    }
    (output_root / "index.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/nse/eod"))
    args = parser.parse_args()
    try:
        result = ingest(args.output_dir)
    except (OSError, urllib.error.URLError, UnicodeError, ValueError, RuntimeError) as exc:
        print(f"ERROR: NSE EOD ingestion failed closed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
