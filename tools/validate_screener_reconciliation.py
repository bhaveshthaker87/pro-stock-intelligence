#!/usr/bin/env python3
"""Validate source-traceable 30-stock x 18-metric Screener reconciliation.

This tool never fetches Screener or bypasses access controls. A generated template
is NOT_TESTED until populated with values from an authorized Screener session/export.
"""
from __future__ import annotations
import argparse, csv, math, re, sys
from datetime import datetime
from pathlib import Path

SYMBOLS = [
 "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","SBIN","BHARTIARTL","ITC","LT","BAJFINANCE",
 "HINDUNILVR","MARUTI","SUNPHARMA","TITAN","NTPC","POWERGRID","AXISBANK","KOTAKBANK","TATASTEEL","ONGC",
 "M&M","WIPRO","HCLTECH","TECHM","ULTRACEMCO","ASIANPAINT","BEL","HAL","TRENT","ADANIPORTS"
]
# Keep this schema aligned exactly with NativeProvider.screenerAudit30(): 18 metrics x 30 stocks.
# Screener page snapshots are fundamentals only and are never represented as live quotes.
METRICS = {
 "marketCap":"INR_CRORE", "pe":"ratio", "industryPE":"ratio", "eps":"INR_PER_SHARE",
 "bookValue":"INR_PER_SHARE", "pb":"ratio", "roe":"percent", "roce":"percent",
 "debtEquity":"ratio", "sales3y":"percent_3Y_GROWTH", "profit3y":"percent_3Y_GROWTH",
 "shareholding":"provider_reported_table", "peg":"ratio", "piotroski":"score_0_9",
 "fii":"percent", "dii":"percent", "pledged":"provider_reported_percent", "promoter":"percent"
}
STATUSES={"VERIFIED_MATCH","VERIFIED_DIFFERENCE","ACCESS_BLOCKED_403","SOURCE_UNAVAILABLE","DATA_MISSING","SYMBOL_MAPPING_ERROR","UNIT_MISMATCH","PERIOD_MISMATCH","NOT_TESTED"}
FIELDS=[
 "symbol","company_name","metric","app_value","screener_value","difference","tolerance",
 "source","source_url","source_timestamp","app_retrieved_at","period","unit","currency",
 "status","evidence_ref","failure_reason"
]

def parse_timestamp(value, field):
 if not value or not str(value).strip(): raise ValueError(f"{field} is required for verified records")
 try:
  dt=datetime.fromisoformat(str(value).strip().replace("Z","+00:00"))
 except ValueError as exc:
  raise ValueError(f"{field} must be ISO-8601") from exc
 if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError(f"{field} must include timezone")
 return dt

def write_template(path):
 path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader()
  for symbol in SYMBOLS:
   for metric,unit in METRICS.items():
    w.writerow({"symbol":symbol,"company_name":"","metric":metric,"source":"AUTHORIZED_SCREENER_EXPORT_REQUIRED",
      "period":"UNSPECIFIED","unit":unit,"currency":"INR","status":"NOT_TESTED",
      "failure_reason":"Awaiting authorized source export"})
 return path

def number(value):
 if value is None or str(value).strip()=="": return None
 raw=str(value).strip().replace("₹","").replace(",","").replace("%","").replace(" ","")
 if raw.startswith("(") and raw.endswith(")"): raw="-"+raw[1:-1]
 try:
  n=float(raw)
  return n if math.isfinite(n) else None
 except ValueError: return None

def validate(path, require_complete=False):
 with Path(path).open(newline="",encoding="utf-8-sig") as f:
  reader=csv.DictReader(f)
  missing=set(FIELDS)-set(reader.fieldnames or [])
  if missing: raise ValueError("Missing columns: "+", ".join(sorted(missing)))
  rows=list(reader)
 expected=len(SYMBOLS)*len(METRICS)
 if len(rows)!=expected: raise ValueError(f"Expected exactly {expected} metric records; found {len(rows)}")
 seen=set(); counts={s:0 for s in STATUSES}
 for i,r in enumerate(rows,2):
  symbol=(r.get("symbol") or "").strip().upper(); metric=(r.get("metric") or "").strip()
  if symbol not in SYMBOLS: raise ValueError(f"Row {i}: unexpected symbol {symbol!r}")
  if metric not in METRICS: raise ValueError(f"Row {i}: unexpected metric {metric!r}")
  key=(symbol,metric)
  if key in seen: raise ValueError(f"Row {i}: duplicate {symbol}/{metric}")
  seen.add(key)
  status=(r.get("status") or "").strip()
  if status not in STATUSES: raise ValueError(f"Row {i}: invalid status {status!r}")
  counts[status]+=1
  if not (r.get("source") or "").strip() or not (r.get("period") or "").strip() or not (r.get("unit") or "").strip():
   raise ValueError(f"Row {i}: source, period and unit are mandatory")
  if r["unit"].strip()!=METRICS[metric]: raise ValueError(f"Row {i}: unit mismatch for {metric}; expected {METRICS[metric]}")
  if status in {"VERIFIED_MATCH","VERIFIED_DIFFERENCE"}:
   if not (r.get("evidence_ref") or "").strip() or not (r.get("source_url") or "").strip():
    raise ValueError(f"Row {i}: verified record requires source_url and evidence_ref")
   parse_timestamp(r.get("source_timestamp"),f"Row {i} source_timestamp")
   parse_timestamp(r.get("app_retrieved_at"),f"Row {i} app_retrieved_at")
   if metric == "shareholding":
    a=str(r.get("app_value") or "").strip(); s=str(r.get("screener_value") or "").strip()
    d=number(r.get("difference")); tol=number(r.get("tolerance"))
    if not a or not s or d is None or tol != 0: raise ValueError(f"Row {i}: verified shareholding table requires both captures and zero/one difference with zero tolerance")
    match=re.sub(r"\\s+"," ",a).casefold()==re.sub(r"\\s+"," ",s).casefold()
    if not math.isclose(d,0.0 if match else 1.0,abs_tol=1e-9): raise ValueError(f"Row {i}: shareholding table difference marker is invalid")
   else:
    a=number(r.get("app_value")); s=number(r.get("screener_value")); d=number(r.get("difference"))
    tol=number(r.get("tolerance"))
    if a is None or s is None or d is None: raise ValueError(f"Row {i}: verified record requires numeric app, Screener and difference values")
    if tol is None or tol < 0: raise ValueError(f"Row {i}: verified record requires non-negative numeric tolerance")
    if not math.isclose(d,a-s,rel_tol=1e-7,abs_tol=1e-6): raise ValueError(f"Row {i}: difference does not equal app_value - screener_value")
    match=abs(a-s)<=tol
   if (status=="VERIFIED_MATCH")!=match: raise ValueError(f"Row {i}: verification status conflicts with tolerance")
 if len(seen)!=expected: raise ValueError("One or more stock/metric combinations are missing")
 verified=counts["VERIFIED_MATCH"]+counts["VERIFIED_DIFFERENCE"]
 result={"status":"PASS" if verified==expected else "PARTIAL","records":len(rows),"verified":verified,
         "unverified":expected-verified,"statusCounts":counts}
 if require_complete and verified!=expected:
  raise ValueError(f"Release gate blocked: {verified}/{expected} metrics independently verified; {expected-verified} remain unverified")
 return result

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--template-out"); ap.add_argument("--input"); ap.add_argument("--require-complete",action="store_true")
 a=ap.parse_args()
 try:
  if a.template_out:
   p=write_template(a.template_out); print(f"Created NOT_TESTED template: {p} ({len(SYMBOLS)*len(METRICS)} rows)"); return 0
  if not a.input: ap.error("provide --template-out or --input")
  result=validate(a.input,a.require_complete)
  print(f"{result['status']}: {result['verified']}/{result['records']} verified; {result['unverified']} unverified")
  for k,v in result["statusCounts"].items():
   if v: print(f"{k}: {v}")
  return 0
 except Exception as e:
  print(str(e),file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
