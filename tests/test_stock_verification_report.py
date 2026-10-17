import csv
import tempfile
import unittest
from pathlib import Path

from tools.verify_stock_data import build_report, read_rows


class StockVerificationReportTests(unittest.TestCase):
    def make_csv(self, rows):
        temp = tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", suffix=".csv", delete=False)
        with temp:
            writer = csv.DictWriter(temp, fieldnames=["source", "symbol", "metric", "value", "unit", "period", "as_of"])
            writer.writeheader()
            writer.writerows(rows)
        self.addCleanup(lambda: Path(temp.name).unlink(missing_ok=True))
        return temp.name

    def rows_for(self, count=30, pe_delta=0):
        rows = []
        for i in range(count):
            symbol = f"TST{i:02d}"
            for source, delta in [("AuthorizedFeed", 0), ("ScreenerExport", pe_delta)]:
                rows += [
                    {"source": source, "symbol": symbol, "metric": "PE", "value": 20 + delta, "unit": "x", "period": "TTM", "as_of": "2026-10-16"},
                    {"source": source, "symbol": symbol, "metric": "EPS", "value": 50, "unit": "INR/share", "period": "TTM", "as_of": "2026-10-16"},
                ]
        return rows

    def test_30_stocks_two_sources_and_core_metrics_can_pass(self):
        rows = read_rows(self.make_csv(self.rows_for()))
        report, passed = build_report(rows)
        self.assertTrue(passed)
        self.assertIn("Fully verified stocks: **30/30**", report)
        self.assertIn("P/E: PASS", report)
        self.assertIn("EPS: PASS", report)

    def test_missing_second_source_fails_closed(self):
        rows = self.rows_for()
        rows = [r for r in rows if not (r["symbol"] == "TST00" and r["source"] == "ScreenerExport")]
        report, passed = build_report(rows)
        self.assertFalse(passed)
        self.assertIn("INCOMPLETE", report)

    def test_material_pe_discrepancy_fails(self):
        rows = read_rows(self.make_csv(self.rows_for(pe_delta=5)))
        report, passed = build_report(rows)
        self.assertFalse(passed)
        self.assertIn("DISCREPANCY", report)

    def test_period_mismatch_fails(self):
        rows = self.rows_for()
        rows[1]["period"] = "FY2025"
        rows = read_rows(self.make_csv(rows))
        report, passed = build_report(rows)
        self.assertFalse(passed)
        self.assertIn("PERIOD MISMATCH", report)

    def test_unknown_units_fail_validation(self):
        rows = self.rows_for()
        rows[0]["unit"] = "million bananas"
        with self.assertRaisesRegex(ValueError, "unexpected unit"):
            read_rows(self.make_csv(rows))


if __name__ == "__main__":
    unittest.main()
