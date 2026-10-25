from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ScreenerXlsxImportTests(unittest.TestCase):
    def test_xlsx_parser_is_bundled_and_loaded_before_dashboard(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        parser = ROOT / "app/src/main/assets/xlsx-import.js"
        self.assertTrue(parser.exists())
        self.assertIn('<script src="xlsx-import.js"></script>', html)
        self.assertIn("window.PSIXlsxImport.parseWorkbook", html)

    def test_import_picker_accepts_xlsx_and_keeps_csv_compatibility(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn('accept=".xlsx,.csv,.txt,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', html)
        self.assertIn("window.PSICsvImport.parseImportCsv", html)
        self.assertIn("window.PSIXlsxImport.parseWorkbook", html)

    def test_screener_workbook_reader_maps_only_explicit_or_derived_values(self):
        source = (ROOT / "app/src/main/assets/xlsx-import.js").read_text(encoding="utf-8")
        for marker in ("Data Sheet", "COMPANY NAME", "Current Price", "Market Capitalization",
                       "Net profit", "Adjusted Equity Shares in Cr", "INR_CRORE",
                       "not a live quote", "does not create OHLCV candles"):
            self.assertIn(marker, source)
        self.assertIn("DecompressionStream('deflate-raw')", source)
        self.assertIn("workbook has no", source)

    def test_screener_workbook_imports_quarterly_results_into_dashboard(self):
        parser = (ROOT / "app/src/main/assets/xlsx-import.js").read_text(encoding="utf-8")
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        for marker in ("const excelDate=x=>", "const quarterLabel=x=>", "const quarterlyRows=[]",
                       "operating_profit", "profit_before_tax", "quarterlyRows,quarterlySummary"):
            self.assertIn(marker, parser)
        self.assertIn("r.quarterlyRows", html)
        self.assertIn("d.quarterly=quarterlyRow.quarterlyRows", html)
        self.assertIn("importedQuarterlyMeta", html)

    def test_xlsx_import_does_not_claim_quarterly_financials_are_candles(self):
        source = (ROOT / "app/src/main/assets/xlsx-import.js").read_text(encoding="utf-8")
        self.assertIn("historyRows:[]", source)
        self.assertIn("historyPeriod:'UNAVAILABLE_IN_WORKBOOK'", source)
        self.assertIn("Quarterly statements remain in the workbook", source)


    def test_screener_xlsx_maps_annual_dividend_and_labels_derived_yield(self):
        source = (ROOT / "app/src/main/assets/xlsx-import.js").read_text(encoding="utf-8")
        self.assertIn("get('Dividend Amount',10)", source)
        self.assertIn("put('dividendAmount',latestDividendAmount,'INR_CRORE'", source)
        self.assertIn("Derived: annual dividend amount / adjusted equity shares", source)
        self.assertIn("Derived: annual dividend per share / workbook current price", source)

if __name__ == "__main__":
    unittest.main()

    def test_nse_udiff_bhavcopy_headers_are_supported_and_mixed_symbols_are_filtered(self):
        source = (ROOT / "app/src/main/assets/csv-import.js").read_text(encoding="utf-8")
        for marker in ("'tckrsymb'", "'tradt'", "'opnpric'", "'hghpric'", "'lwpric'",
                       "'clspric'", "'ttltradgvol'", "mixed-symbol candles were rejected",
                       "rows for other symbols were excluded"):
            self.assertIn(marker, source)

    def test_provider_gateway_has_bounded_safe_retry_and_no_stale_quote_fallback(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        for marker in ("for (attempt in 0..2)", "code == 429 || code in 500..599",
                       "never substitute stale cached quotes", "HTTP 401", "HTTP 403",
                       "malformed JSON", "2 MB safety limit"):
            self.assertIn(marker, source)

    def test_release_version_is_aligned_across_android_and_dashboard(self):
        gradle = (ROOT / "app/build.gradle").read_text(encoding="utf-8")
        native = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("versionCode 80; versionName '40.81'", gradle)
        self.assertIn("V40.81 AUTHORIZED GATEWAY + CSV OHLCV FALLBACK", native)
        self.assertIn("V40.81 AUTHORIZED GATEWAY + CSV OHLCV FALLBACK", html)
