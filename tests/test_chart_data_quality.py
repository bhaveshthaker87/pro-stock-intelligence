"""Behavioral tests for chart-bar normalization and indicator safety in the shipped UI."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
HTML = ROOT / "app/src/main/assets/index.html"


@unittest.skipUnless(shutil.which("node"), "Node.js is required for JavaScript behavior tests")
class ChartDataQualityTests(unittest.TestCase):
    def run_clean_rows(self, rows):
        script = r'''const fs=require('fs');
const html=fs.readFileSync(process.argv[1],'utf8');
const start=html.indexOf('function safeNum(v)');
const end=html.indexOf('\nfunction esc(x)',start);
if(start<0||end<0)throw new Error('chart normalizer not found');
const block=html.slice(start,end);
const finite='function finite(v){return typeof v===\'number\'&&Number.isFinite(v)}';
const clean=block.slice(block.indexOf('function cleanRows(rows){'));
const safe='function safeNum(v){const n=Number(v);return Number.isFinite(n)?n:null}';
const fn=new Function(finite+';'+safe+';'+clean+';return cleanRows;')();
const rows=JSON.parse(process.argv[2]);
process.stdout.write(JSON.stringify(fn(rows)));'''
        result = subprocess.run(
            ["node", "-e", script, str(HTML), json.dumps(rows)],
            text=True, capture_output=True, check=True, timeout=10,
        )
        return json.loads(result.stdout)

    def test_sorts_epoch_seconds_and_deduplicates_timestamps(self):
        rows = [
            {"time": 1760000002, "open": 102, "high": 104, "low": 101, "close": 103, "volume": 10},
            {"time": 1760000001, "open": 100, "high": 102, "low": 99, "close": 101, "volume": 9},
            {"time": 1760000001, "open": 100, "high": 103, "low": 99, "close": 102, "volume": 11},
        ]
        out = self.run_clean_rows(rows)
        self.assertEqual(len(out), 2)
        self.assertEqual([r["time"] for r in out], [1760000001000, 1760000002000])
        self.assertEqual(out[0]["close"], 102)  # last duplicate wins deterministically

    def test_rejects_impossible_ohlc_and_negative_volume(self):
        rows = [
            {"time": 1760000001000, "open": 100, "high": 99, "low": 98, "close": 100, "volume": 1},
            {"time": 1760000002000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": -1},
            {"time": 1760000003000, "open": 100, "high": 102, "low": 99, "close": 101, "volume": 0},
        ]
        out = self.run_clean_rows(rows)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["close"], 101)

    def test_flat_market_rsi_is_neutral_not_overbought(self):
        rows = []
        start = 1750000000
        for i in range(20):
            rows.append({"time": start + i * 86400, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10})
        out = self.run_clean_rows(rows)
        self.assertEqual(out[14]["rsi14"], 50)
        self.assertEqual(out[-1]["rsi14"], 50)

    def test_iso_dates_are_normalized_to_epoch_milliseconds(self):
        out = self.run_clean_rows([{"date": "2025-01-02T00:00:00Z", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 3}])
        self.assertEqual(out[0]["time"], 1735776000000)

    def test_financial_number_parser_preserves_zero_and_indian_formats(self):
        script = r"""const fs=require('fs');const html=fs.readFileSync(process.argv[1],'utf8');
const m=html.match(/function trendParse\(v\)\{[\\s\\S]*?\\n\}/);if(!m)throw new Error('trendParse missing');
const fn=new Function(m[0]+';return trendParse;')();
const values=['₹2,125.50','2,125.50','1.25','0.00','-3.40','12.5%','1,25,000 Cr','(3.40)','—','N/A',''];
process.stdout.write(JSON.stringify(values.map(fn)));"""
        result = subprocess.run(["node", "-e", script, str(HTML)], text=True, capture_output=True, check=True, timeout=10)
        self.assertEqual(json.loads(result.stdout), [2125.5, 2125.5, 1.25, 0, -3.4, 12.5, 125000, -3.4, None, None, None])

if __name__ == "__main__":
    unittest.main()
