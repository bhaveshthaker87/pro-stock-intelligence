#!/usr/bin/env python3
"""Compare two or more authorized stock-data exports without inventing values.

Input CSV columns:
source,symbol,metric,value,unit,period,as_of
Each source/symbol/metric should have one row. Export data from permitted sources
(e.g. an authorized provider gateway and an authorized Screener export). This tool
does not log in, scrape sites, or treat synthetic fixtures as market evidence.
"""
import argparse
import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

REQUIRED = {"source", "symbol", "metric", "value", "unit", "period", "as_of"}
UNITS = {
    "pe": {"x", "times", "ratio"},
    "eps": {"inr/share", "₹/share", "rupees/share", "rs/share"},
    "marketcap": {"inr crore", "₹ crore", "crore inr", "cr"},
    "roe": {"%", "percent", "percentage"},
    "roce": {"%", "percent", "percentage"},
    "price": {"inr", "₹", "rs"},
}
CORE = ("pe", "eps")
TOLERANCE_PCT = 5.0


def key(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").strip().lower())


def parse_number(value):
    try:
        number = float(str(value).strip().replace(",", "").replace("₹", "").replace("%", ""))
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def read_rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = {(x or "").strip().lower() for x in (reader.fieldnames or [])}
        missing = REQUIRED - fields
        if missing:
            raise ValueError("CSV missing required columns: " + ", ".join(sorted(missing)))
        # Preserve original headers while accepting case/space variants.
        header_map = {(x or "").strip().lower(): x for x in reader.fieldnames}
        rows = []
        for line, raw in enumerate(reader, 2):
            row = {name: (raw.get(header_map[key(name)]) or "").strip() for name in REQUIRED}
            row["symbol"] = row["symbol"].upper().replace(".NS", "").replace(".BO", "")
            row["metric"] = key(row["metric"])
            row["value_num"] = parse_number(row["value"])
            row["line"] = line
            if not row["source"] or not row["symbol"] or not row["metric"]:
                raise ValueError(f"CSV line {line}: source, symbol and metric are required")
            if row["value_num"] is None:
                raise ValueError(f"CSV line {line}: invalid numeric value {row['value']!r}")
            if not row["unit"] or not row["period"] or not row["as_of"]:
                raise ValueError(f"CSV line {line}: unit, period and as_of are required")
            allowed = UNITS.get(row["metric"])
            if allowed and key(row["unit"]) not in {key(x) for x in allowed}:
                raise ValueError(f"CSV line {line}: unexpected unit {row['unit']!r} for {row['metric']}")
            rows.append(row)
    return rows


def build_report(rows, min_stocks=30):
    grouped = defaultdict(list)
    symbols = sorted({r["symbol"] for r in rows})
    for row in rows:
        grouped[(row["symbol"], row["metric"])].append(row)
    source_names = sorted({r["source"] for r in rows})
    findings = []
    verified = 0
    for symbol in symbols:
        per_metric = []
        stock_ok = len(source_names) >= 2
        for metric in CORE:
            values = grouped.get((symbol, metric), [])
            sources = {r["source"] for r in values}
            if len(values) < 2 or len(sources) < 2:
                per_metric.append(f"{metric.upper()}: INCOMPLETE (need >=2 independent sources)")
                stock_ok = False
                continue
            periods = {r["period"] for r in values}
            units = {key(r["unit"]) for r in values}
            numbers = [r["value_num"] for r in values]
            if len(periods) != 1:
                per_metric.append(f"{metric.upper()}: PERIOD MISMATCH ({', '.join(sorted(periods))})")
                stock_ok = False
                continue
            if len(units) != 1:
                per_metric.append(f"{metric.upper()}: UNIT MISMATCH ({', '.join(sorted({r['unit'] for r in values}))})")
                stock_ok = False
                continue
            spread_pct = (max(numbers) - min(numbers)) / max(max(abs(x) for x in numbers), 1.0) * 100
            if spread_pct > TOLERANCE_PCT:
                per_metric.append(f"{metric.upper()}: DISCREPANCY {spread_pct:.2f}% (> {TOLERANCE_PCT:.1f}%)")
                stock_ok = False
            else:
                asofs = ", ".join(f"{r['source']}={r['as_of']}" for r in values)
                per_metric.append(f"{metric.upper()}: PASS ({spread_pct:.2f}% spread; {asofs})")
        if stock_ok:
            verified += 1
        findings.append((symbol, stock_ok, per_metric))
    passed = len(symbols) >= min_stocks and verified == len(symbols) and len(source_names) >= 2
    lines = [
        "# Stock Data Verification Report",
        "",
        f"- Result: **{'PASS' if passed else 'FAIL / INCOMPLETE'}**",
        f"- Stocks supplied: **{len(symbols)}** (minimum required: {min_stocks})",
        f"- Independent source labels: **{len(source_names)}** ({', '.join(source_names) if source_names else 'none'})",
        f"- Fully verified stocks: **{verified}/{len(symbols)}**",
        f"- Core fields: **P/E and EPS**",
        f"- Numeric agreement threshold: **{TOLERANCE_PCT:.1f}% relative spread**",
        "- All values are from the supplied CSV; this report does not independently fetch or certify source data.",
        "",
        "| Symbol | Status | P/E | EPS |",
        "|---|---|---|---|",
    ]
    for symbol, ok, parts in findings:
        lines.append(f"| {symbol} | {'PASS' if ok else 'CHECK'} | {parts[0]} | {parts[1]} |")
    lines += ["", "## Audit notes", ""]
    for row in rows:
        lines.append(f"- {row['symbol']} / {row['metric'].upper()} / {row['source']}: value={row['value']} {row['unit']}; period={row['period']}; as-of={row['as_of']} (CSV line {row.get('line', 'unknown')}).")
    lines += ["", "## Interpretation", "", "PASS means the supplied records meet this script's structural and cross-source checks. It does not prove that a source is licensed, authentic, complete, or current; verify source permissions and timestamps separately."]
    return "\n".join(lines) + "\n", passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", help="Authorized, normalized source export CSV")
    parser.add_argument("--output", default="stock-verification-report.md")
    parser.add_argument("--min-stocks", type=int, default=30)
    args = parser.parse_args()
    try:
        rows = read_rows(args.input_csv)
        report, passed = build_report(rows, args.min_stocks)
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Wrote {args.output}; {len({r['symbol'] for r in rows})} symbols; status={'PASS' if passed else 'FAIL / INCOMPLETE'}")
        return 0 if passed else 2
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
