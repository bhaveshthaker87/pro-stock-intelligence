import csv, json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SYMBOLS=[
 "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","SBIN","BHARTIARTL","ITC","LT","BAJFINANCE",
 "HINDUNILVR","MARUTI","SUNPHARMA","TITAN","NTPC","POWERGRID","AXISBANK","KOTAKBANK","TATASTEEL","ONGC",
 "M&M","WIPRO","HCLTECH","TECHM","ULTRACEMCO","ASIANPAINT","BEL","HAL","TRENT","ADANIPORTS"
]
METRIC_HEADERS={
 "marketCap":"Market Capitalization","pe":"Stock P/E","industryPE":"Industry PE","eps":"EPS",
 "bookValue":"Book Value","pb":"Price to book value","roe":"ROE","roce":"ROCE",
 "debtEquity":"Debt to equity","sales3y":"Sales growth 3Years","profit3y":"Profit growth 3Years",
 "shareholding":"Shareholding","peg":"PEG Ratio","piotroski":"Piotroski score",
 "fii":"FII holding","dii":"DII holding","pledged":"Pledged percentage","promoter":"Promoter holding"
}

class ScreenerReconciliationBuilderTests(unittest.TestCase):
 def test_builds_540_independent_comparisons_from_two_captures(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); app_rows=[]; csv_path=root/"screener-export.csv"
   headers=["NSE Code","Name",*METRIC_HEADERS.values()]
   with csv_path.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=headers);w.writeheader()
    for symbol in SYMBOLS:
     vals={name:("Promoter 50%; FII 10%" if metric=="shareholding" else "100") for metric,name in METRIC_HEADERS.items()}
     w.writerow({"NSE Code":symbol,"Name":symbol+" Ltd",**vals})
     app_rows.append({"symbol":symbol,"name":symbol+" Ltd","fetchedAtEpochMs":1794762000000,
       "metrics":{metric:{"appValue":("Promoter 50%; FII 10%" if metric=="shareholding" else 100),
         "period":"FY2026 / latest provider-reported"} for metric in METRIC_HEADERS}})
   app_path=root/"app-snapshot.json"; app_path.write_text(json.dumps({"rows":app_rows}),encoding="utf-8")
   out=root/"reconciliation.csv"
   cmd=[sys.executable,str(ROOT/"tools/build_screener_reconciliation.py"),
        "--app-snapshot",str(app_path),"--screener-csv",str(csv_path),"--output",str(out),
        "--screener-exported-at","2026-11-15T12:00:00+05:30","--require-complete"]
   p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
   self.assertEqual(p.returncode,0,p.stderr+"\n"+p.stdout)
   with out.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
   self.assertEqual(len(rows),540)
   self.assertTrue(all(r["status"]=="VERIFIED_MATCH" for r in rows))

if __name__=="__main__": unittest.main()
