#!/usr/bin/env python3
"""Build the 30-stock x 18-metric audit from an app parser snapshot and a separate Screener CSV export.

The script never fetches Screener, logs in, or bypasses access controls. It counts a metric as verified
only when both independent captures contain a comparable value with a known unit and explicit
source timestamps. Missing columns/values remain DATA_MISSING.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, sys
from datetime import datetime, timezone
from pathlib import Path

from validate_screener_reconciliation import FIELDS, METRICS, SYMBOLS, validate

ALIASES = {
 "symbol": ["symbol", "nse code", "nse symbol", "stock symbol"],
 "name": ["name", "company", "company name"],
 "marketCap": ["market capitalization", "market cap", "marketcap"],
 "pe": ["stock p/e", "price to earning", "p/e", "pe"],
 "industryPE": ["industry pe", "industry p/e", "industrype"],
 "eps": ["eps", "earning per share", "earnings per share"],
 "bookValue": ["book value", "bookvalue"],
 "pb": ["price to book value", "p/b", "pb"],
 "roe": ["roe", "return on equity"],
 "roce": ["roce", "return on capital employed"],
 "debtEquity": ["debt to equity", "debt/equity", "debt equity"],
 "sales3y": ["sales growth 3years", "sales growth 3 years", "sales growth 3y", "sales3y"],
 "profit3y": ["profit growth 3years", "profit growth 3 years", "profit growth 3y", "profit3y"],
 "shareholding": ["shareholding", "shareholding pattern"],
 "peg": ["peg ratio", "peg"],
 "piotroski": ["piotroski score", "piotroski"],
 "fii": ["fii holding", "fii", "foreign institutional holding"],
 "dii": ["dii holding", "dii", "domestic institutional holding"],
 "pledged": ["pledged percentage", "pledged", "pledged promoter holding"],
 "promoter": ["promoter holding", "promoter"],
}
TOLERANCE = {"marketCap": 1.0, "eps": 0.01, "bookValue": 0.01, "roe": 0.1, "roce": 0.1,
             "sales3y": 0.1, "profit3y": 0.1, "fii": 0.1, "dii": 0.1, "promoter": 0.1, "pledged": 0.1}

def norm_header(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").replace("%", " percent").lower()).strip()

def number(value):
    if value is None: return None
    raw=str(value).strip()
    if not raw or raw in {"-","—","NA","N/A","null"}: return None
    raw=raw.replace("₹","").replace(",","").replace("%","").replace(" ","")
    raw=re.sub(r"(?i)(cr|crore|x)$","",raw)
    if raw.startswith("(") and raw.endswith(")"): raw="-"+raw[1:-1]
    try:
        v=float(raw)
        return v if math.isfinite(v) else None
    except ValueError: return None

def iso_from_epoch(value):
    try:
        n=int(value)
        if n > 10**12: n=n/1000
        return datetime.fromtimestamp(n,timezone.utc).isoformat()
    except (TypeError,ValueError,OverflowError,OSError):
        return ""

def load_export(path):
    with Path(path).open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        rows=list(reader)
        headers={norm_header(h):h for h in (reader.fieldnames or [])}
    if not rows: raise ValueError("Screener export CSV contains no data rows")
    symbol_col=next((headers[norm_header(a)] for a in ALIASES["symbol"] if norm_header(a) in headers),None)
    if not symbol_col: raise ValueError("Export needs an NSE Code / Symbol column; do not infer symbols from company names")
    return rows,headers,symbol_col

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app-snapshot",required=True,help="JSON downloaded from the app's Audit 30 stocks panel")
    ap.add_argument("--screener-csv",required=True,help="CSV exported directly from Screener.in")
    ap.add_argument("--output",default="data/screener/30-stock-reconciliation.csv")
    ap.add_argument("--screener-exported-at",required=True,help="ISO-8601 timestamp with timezone from when the Screener CSV was exported")
    ap.add_argument("--require-complete",action="store_true")
    args=ap.parse_args()
    try:
        exported_at=datetime.fromisoformat(args.screener_exported_at.replace("Z","+00:00"))
        if exported_at.tzinfo is None: raise ValueError("--screener-exported-at must include timezone")
        app=json.loads(Path(args.app_snapshot).read_text(encoding="utf-8"))
        if app.get("snapshotOrigin") == "SCREENER_CSV_IMPORT_PARSER":
            ref_hash=hashlib.sha256(Path(args.screener_csv).read_bytes()).hexdigest()
            imported_hash=str(app.get("sourceExportSha256") or "")
            if not imported_hash:
                raise ValueError("Imported-parser snapshot has no SHA-256 fingerprint; export a second independent Screener CSV and rebuild the app snapshot.")
            if ref_hash == imported_hash:
                raise ValueError("Circular audit blocked: the reference CSV is the same file used to create the app parser snapshot. Export a second Screener CSV separately.")
        app_rows={str(r.get("symbol","")).upper():r for r in app.get("rows",[])}
        csv_rows,headers,symbol_col=load_export(args.screener_csv)
        ref_by_symbol={str(r.get(symbol_col,"")).strip().upper(): (r,i) for i,r in enumerate(csv_rows,2)}
        field_cols={}
        for metric,aliases in ALIASES.items():
            if metric in {"symbol","name"}: continue
            col=next((headers[norm_header(a)] for a in aliases if norm_header(a) in headers),None)
            field_cols[metric]=col
        out=[]; missing_symbols=[]
        for symbol in SYMBOLS:
            app_row=app_rows.get(symbol)
            ref=ref_by_symbol.get(symbol)
            if not ref: missing_symbols.append(symbol)
            ref_row,ref_line=ref if ref else ({},0)
            for metric,unit in METRICS.items():
                parsed=(app_row or {}).get("metrics",{}).get(metric,{})
                app_value=parsed.get("appValue",parsed.get("value"))
                col=field_cols.get(metric)
                raw_ref=ref_row.get(col) if col else None
                a=number(app_value); b=number(raw_ref)
                # shareholding is a provider-reported table, not a scalar. Do not
                # pretend a numeric comparison exists unless both captures are numeric.
                status="DATA_MISSING"; difference=""; tolerance=""
                if metric=="shareholding":
                    av=json.dumps(app_value,sort_keys=True,ensure_ascii=False) if isinstance(app_value,(dict,list)) else str(app_value or "").strip()
                    bv=str(raw_ref or "").strip()
                    if av and bv:
                        status="VERIFIED_MATCH" if re.sub(r"\s+"," ",av).casefold()==re.sub(r"\s+"," ",bv).casefold() else "VERIFIED_DIFFERENCE"
                        difference="0" if status=="VERIFIED_MATCH" else "1"; tolerance="0"
                    else: av=""; bv=""
                else:
                    av="" if a is None else str(a); bv="" if b is None else str(b)
                    if a is not None and b is not None:
                        tolerance=TOLERANCE.get(metric,0.01)
                        difference=a-b
                        status="VERIFIED_MATCH" if abs(difference)<=tolerance else "VERIFIED_DIFFERENCE"
                meta=parsed
                period=str(meta.get("period") or "PERIOD_NOT_LABELLED")
                fetched=iso_from_epoch((app_row or {}).get("fetchedAtEpochMs"))
                name=str(ref_row.get(headers.get(norm_header("name"),""),"") or (app_row or {}).get("name",""))
                out.append({
                    "symbol":symbol,"company_name":name,"metric":metric,"app_value":av,
                    "screener_value":bv,"difference":difference,"tolerance":tolerance,
                    "source":"Screener.in official exported screen CSV","source_url":f"https://www.screener.in/company/{symbol}/",
                    "source_timestamp":exported_at.isoformat(),"app_retrieved_at":fetched,
                    "period":period,"unit":unit,"currency":"INR","status":status,
                    "evidence_ref":f"{Path(args.screener_csv).name}:row-{ref_line}" if ref else "",
                    "failure_reason":"" if status.startswith("VERIFIED_") else ("Symbol absent from export" if not ref else ("Metric column absent from export" if not col else "Value missing in one or both captures"))
                })
        dest=Path(args.output); dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
        result=validate(dest,args.require_complete)
        print(json.dumps({**result,"output":str(dest),"missingSymbols":missing_symbols},indent=2))
        return 0
    except Exception as exc:
        print(str(exc),file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
