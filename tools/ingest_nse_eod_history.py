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

REPORTS_URL = "https://www.nseindia.in/all-reports"
OFFICIAL_HOSTS = {"nseindia.com", "www.nseindia.com", "nseindia.in", "www.nseindia.in", "nsearchives.nseindia.com"}
ARCHIVE_BASE = "https://nsearchives.nseindia.com/content/cm/"
REPORT_RE = re.compile(r"BhavCopy_NSE_CM_0_0_0_(\d{8})_F_0000\.csv\.zip", re.I)
USER_AGENT = "Mozilla/5.0 (compatible; ProStockIntelligence-EOD/1.0)"


class LinkParser(HTMLParser):
    """Collect link text and all attributes because NSE report controls are not always anchors."""
    def __init__(self):
        super().__init__()
        self.links = []
        self._attrs = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        values = [str(value) for _, value in attrs if value]
        if tag.lower() in {"a", "button", "input"} or values:
            self._attrs = values
            self._text = []

    def handle_data(self, data):
        if self._attrs is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if self._attrs is not None:
            self.links.append((self._attrs, " ".join(self._text).strip()))
            self._attrs = None
            self._text = []


def _official_report_url(value: str, base_url: str) -> tuple[str, str] | None:
    match = REPORT_RE.search(value)
    if not match:
        return None
    candidate = value.strip()
    if candidate.lower().startswith(("javascript:", "#")):
        candidate = ""
    # A bare filename is not a page-relative URL; resolve it only against
    # the explicitly configured official NSE archive directory.
    if candidate and "://" not in candidate and "/" not in candidate and "\\" not in candidate:
        candidate = ""
    if candidate:
        url = urljoin(base_url, candidate)
    else:
        url = urljoin(ARCHIVE_BASE, match.group(0))
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS:
        return None
    return match.group(1), url


def discover_report_url(html: str, base_url: str = REPORTS_URL) -> str:
    parser = LinkParser()
    parser.feed(html)
    # Keep explicit URLs ahead of inferred archive URLs for the same trading date.
    # Never infer an archive URL from a filename embedded in a rejected external URL.
    candidates = []
    for attrs, label in parser.links:
        for value in attrs + [label]:
            item = _official_report_url(value, base_url)
            if item:
                explicit = "://" in value or value.strip().startswith(("/", "./", "../"))
                candidates.append((item[0], item[1], explicit))

    # Some NSE pages render a bare filename in inline state/text instead of a link.
    for match in REPORT_RE.finditer(html):
        line_start = max(html.rfind("<", 0, match.start()), html.rfind(">", 0, match.start())) + 1
        prefix = html[line_start:match.start()]
        # If the filename is part of any URL (including a disallowed host), do not
        # turn it into a different, guessed official URL.
        if re.search(r"(?:https?://|/)[^\\s\"'<>]*$", prefix, re.I):
            continue
        item = _official_report_url(match.group(0), base_url)
        if item:
            candidates.append((item[0], item[1], False))

    if not candidates:
        raise ValueError("NSE All Reports page did not expose a matching official CM-UDiFF ZIP link")
    latest_date = max(item[0] for item in candidates)
    latest = [item for item in candidates if item[0] == latest_date]
    explicit = [item for item in latest if item[2]]
    return sorted(explicit or latest, key=lambda item: item[1])[0][1]


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
        if final.scheme != "https" or final.hostname not in OFFICIAL_HOSTS:
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
    if daily_path.exists() and daily_path.read_bytes() != csv_text.encode("utf-8"):
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
