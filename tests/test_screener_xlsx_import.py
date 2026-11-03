from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LegacySpreadsheetImportRemovalTests(unittest.TestCase):
    def test_csv_xlsx_import_modules_and_ui_are_removed(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        native = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertFalse((ROOT / "app/src/main/assets/csv-import.js").exists())
        self.assertFalse((ROOT / "app/src/main/assets/xlsx-import.js").exists())
        for marker in ('id="csvFile"', 'id="csvSource"', 'id="xlsxFile"', 'Import CSV', 'Import XLSX'):
            self.assertNotIn(marker, html)
        for marker in ("PSICsvImport", "PSIXlsxImport", "mergeImportedCsvData", "useImportedCsv"):
            self.assertNotIn(marker, html)
        self.assertNotIn("onShowFileChooser", native)
        self.assertNotIn("csvPickerRequestCode", native)

    def test_internal_json_provider_and_official_eod_pipeline_remain_available(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        native = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("/api/history", native)
        self.assertIn("jsonResponse", native)
        self.assertIn("official NSE EOD", html.lower() if "official NSE EOD" in html else "official nse eod")
