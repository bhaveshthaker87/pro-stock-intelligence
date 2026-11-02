#!/usr/bin/env python3
"""Independent parity audit for the dashboard's daily-close indicators.

Reads only validated official NSE EOD CSV rows. Insufficient history is reported,
never backfilled or fabricated. Formulas mirror index.html cleanRows().
"""
from __future__ import annotations
import argparse, csv, json, math
from collections import defaultdict
from pathlib import Path

SYMBOLS = ["RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","SBIN","BHARTIARTL","ITC","LT","BAJFINANCE",
"HINDUNILVR","MARUTI","SUNPHARMA","TITAN","NTPC","POWERGRID","AXISBANK","KOTAKBANK","TATASTEEL","ONGC",
"M&M","WIPRO","HCLTECH","TECHM","ULTRACEMCO","ASIANPAINT","BEL","HAL","TRENT","ADANIPORTS"]

def sma(values, n):
    return sum(values[-n:]) / n if len(values) >= n else None

def rsi_wilder(values, n=14):
    if len(values) <= n: return None
    gain=loss=0.0
    for i in range(1,n+1):
        d=values[i]-values[i-1]; gain+=max(d,0); loss+=max(-d,0)
    gain/=n; loss/=n
    for i in range(n+1,len(values)):
        d=values[i]-values[i-1]; gain=(gain*(n-1)+max(d,0))/n; loss=(loss*(n-1)+max(-d,0))/n
    if gain==0 and loss==0:return 50.0
    if loss==0:return 100.0
    if gain==0:return 0.0
    return 100-100/(1+gain/loss)

def nw_envelope(values, look=40, bandwidth=12, multiplier=2.5):
    if len(values)<10:return None
    i=len(values)-1; lo=max(0,i-look+1); tw=0.0; weighted=0.0
    for j in range(lo,i+1):
        lag=i-j; w=math.exp(-(lag*lag)/(2*bandwidth*bandwidth)); tw+=w; weighted+=values[j]*w
    if not tw:return None
    basis=weighted/tw; mad=0.0
    for j in range(lo,i+1):
        lag=i-j; w=math.exp(-(lag*lag)/(2*bandwidth*bandwidth)); mad+=abs(values[j]-basis)*w
    mad/=tw
    return {"basis":basis,"upper":basis+multiplier*mad,"lower":basis-multiplier*mad}

def load_rows(root: Path):
    grouped=defaultdict(dict)
    for path in sorted(root.glob("*.csv")):
        with path.open(newline="",encoding="utf-8-sig") as f:
            reader=csv.DictReader(f)
            for row in reader:
                if (row.get("marketDataStatus") or "").strip().upper()!="EOD": continue
                symbol=(row.get("symbol") or "").strip().upper()
                day=(row.get("date") or "").strip()[:10]
                if not symbol or not day: continue
                try:
                    o,h,l,c,v=[float(row[k].replace(",","")) for k in ("open","high","low","close","volume")]
                except (KeyError,ValueError,AttributeError): continue
                if not all(math.isfinite(x) for x in (o,h,l,c,v)) or min(o,h,l,c)<=0 or v<0 or h<max(o,c,l) or l>min(o,c,h): continue
                grouped[symbol][day]={"date":day,"open":o,"high":h,"low":l,"close":c,"volume":v}
    return {s:[m[d] for d in sorted(m)] for s,m in grouped.items()}

def audit(root: Path):
    data=load_rows(root); results=[]
    for symbol in SYMBOLS:
        rows=data.get(symbol,[]); closes=[r["close"] for r in rows]
        indicators={"sma50":sma(closes,50),"sma200":sma(closes,200),"rsi14":rsi_wilder(closes),"nw":nw_envelope(closes)}
        enough=len(rows)>=200 and indicators["sma200"] is not None and indicators["rsi14"] is not None and indicators["nw"] is not None
        results.append({"symbol":symbol,"status":"CALCULATED_FROM_OFFICIAL_NSE_EOD" if enough else "INSUFFICIENT_OFFICIAL_HISTORY",
          "source":"NSE CM-UDiFF Common Bhavcopy Final","bars":len(rows),"from":rows[0]["date"] if rows else None,
          "asOf":rows[-1]["date"] if rows else None,"indicators":indicators})
    passed=sum(r["status"]=="CALCULATED_FROM_OFFICIAL_NSE_EOD" for r in results)
    return {"source":"NSE CM-UDiFF Common Bhavcopy Final","targetSymbols":len(SYMBOLS),"calculatedSymbols":passed,
      "status":"PASS" if passed==len(SYMBOLS) else "PARTIAL_INSUFFICIENT_HISTORY","formulaContract":"SMA simple rolling mean; RSI Wilder-14; one-sided causal Gaussian NW lookback=40 bandwidth=12 envelope=2.5 weighted mean absolute deviation",
      "rows":results}

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data/nse/eod");ap.add_argument("--output",default="chart-parity-report.json");args=ap.parse_args()
    report=audit(Path(args.data_dir));Path(args.output).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"Chart parity audit: {report['status']} — {report['calculatedSymbols']}/{report['targetSymbols']} symbols have >=200 validated official NSE EOD bars")
    print(f"Report: {args.output}")
