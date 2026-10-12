import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]

class CsvImportTests(unittest.TestCase):
    def run_js(self, code):
        p = subprocess.run(["node", "-e", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return json.loads(p.stdout)

    def test_screener_csv_maps_symbols_and_core_metrics(self):
        code = r'''const p=require("./app/src/main/assets/csv-import.js"); const x=p.parseImportCsv("Name,NSE Code,Market Capitalization,Stock P/E,EPS in Rs,ROCE,ROE,Debt to equity\nInfosys,INFY,650000,25.4,55,34.2,29.1,0.04",{source:"Screener.in CSV"}); console.log(JSON.stringify(x.records[0]));'''
        row = self.run_js(code)
        self.assertEqual(row["symbol"], "INFY")
        self.assertEqual(row["fields"]["marketCap"], 650000)
        self.assertEqual(row["meta"]["marketCap"]["unit"], "INR_CRORE")
        self.assertEqual(row["fields"]["pe"], 25.4)
        self.assertEqual(row["fields"]["eps"], 55)

    def test_quoted_commas_and_newlines_are_parsed(self):
        code = r'''const p=require("./app/src/main/assets/csv-import.js"); console.log(JSON.stringify(p.parseCsv('Name,NSE Code,Notes\r\n"Infosys, Ltd",INFY,"first line\nsecond line"')));'''
        x = self.run_js(code)
        self.assertEqual(x["rows"][0][0], "Infosys, Ltd")
        self.assertIn("second line", x["rows"][0][2])

    def test_unknown_market_cap_unit_is_rejected_for_moneycontrol(self):
        code = r'''const p=require("./app/src/main/assets/csv-import.js"); const x=p.parseImportCsv("Symbol,Market Cap,PE\nINFY,650000,25",{source:"Moneycontrol CSV"}); console.log(JSON.stringify(x.records[0]));'''
        row = self.run_js(code)
        self.assertNotIn("marketCap", row["fields"])
        self.assertEqual(row["fields"]["pe"], 25)

    def test_invalid_values_are_not_parsed_as_numbers(self):
        code = r'''const p=require("./app/src/main/assets/csv-import.js"); console.log(JSON.stringify({bad:p.strictNumber("25x","PE","pe","Moneycontrol CSV"), blank:p.strictNumber("—","PE","pe","Moneycontrol CSV"), neg:p.strictNumber("(12.5)","EPS","eps","Screener.in CSV")}));'''
        x = self.run_js(code)
        self.assertIsNone(x["bad"])
        self.assertIsNone(x["blank"])
        self.assertEqual(x["neg"], -12.5)

    def test_historical_ohlcv_is_sorted_and_validated(self):
        code = r'''const p=require("./app/src/main/assets/csv-import.js"); const lines=["Date,Open,High,Low,Close,Volume"]; for(let i=24;i>=0;i--){const d=new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10);const c=100+i;lines.push(`${d},${c-1},${c+2},${c-2},${c},1000`)} console.log(JSON.stringify(p.parseImportCsv(lines.join("\n"),{source:"User CSV",selectedSymbol:"INFY"})));'''
        x = self.run_js(code)
        self.assertEqual(len(x["historyRows"]), 25)
        self.assertLess(x["historyRows"][0]["time"], x["historyRows"][-1]["time"])

    def test_ambiguous_multirow_export_without_symbols_is_rejected(self):
        code = r'''const p=require("./app/src/main/assets/csv-import.js"); try { p.parseImportCsv("Name,PE\nInfosys,25\nTCS,30",{source:"User CSV"}); console.log(JSON.stringify({ok:true})); } catch(e) { console.log(JSON.stringify({ok:false,error:e.message})); }'''
        x = self.run_js(code)
        self.assertFalse(x["ok"])

    def test_duplicate_symbol_rows_are_skipped_as_ambiguous(self):
        code = "const p=require('./app/src/main/assets/csv-import.js'); const x=p.parseImportCsv('Name,NSE Code,Stock P/E\\nInfosys,INFY,25\\nInfosys duplicate,INFY,26\\nTata Consultancy Services,TCS,30',{source:'Screener.in CSV'}); console.log(JSON.stringify(x));"
        x = self.run_js(code)
        self.assertEqual([r["symbol"] for r in x["records"]], ["TCS"])
        self.assertTrue(any("Duplicate symbol rows" in w for w in x["warnings"]))

if __name__ == "__main__":
    unittest.main()
