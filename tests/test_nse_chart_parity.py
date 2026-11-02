import importlib.util
import math
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("chart_audit",ROOT/"tools/validate_nse_chart_parity.py")
MODULE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MODULE)

class NseChartParityTests(unittest.TestCase):
    def test_sma_rsi_and_nw_are_deterministic_and_causal(self):
        values=[100.0+i for i in range(220)]
        self.assertAlmostEqual(MODULE.sma(values,50),194.5,places=9)
        self.assertEqual(MODULE.rsi_wilder(values),100.0)
        a=MODULE.nw_envelope(values)
        b=MODULE.nw_envelope(values+[9999.0])
        self.assertNotAlmostEqual(a["basis"],b["basis"],places=5)
        self.assertLess(a["lower"],a["basis"])
        self.assertGreater(a["upper"],a["basis"])
    def test_official_eod_dataset_reports_insufficient_history_instead_of_fabricating(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"2026-01-01.csv"
            with p.open("w",newline="",encoding="utf-8") as f:
                f.write("symbol,date,open,high,low,close,volume,marketDataStatus\n")
                for i in range(20):
                    c=100+i
                    f.write(f"INFY,2026-01-{i+1:02d},{c},{c+1},{c-1},{c},1000,EOD\n")
            result=MODULE.audit(Path(tmp))
            infy=next(x for x in result["rows"] if x["symbol"]=="INFY")
            self.assertEqual(infy["status"],"INSUFFICIENT_OFFICIAL_HISTORY")
            self.assertIsNone(infy["indicators"]["sma200"])
            self.assertEqual(result["targetSymbols"],30)

if __name__=="__main__":unittest.main()
