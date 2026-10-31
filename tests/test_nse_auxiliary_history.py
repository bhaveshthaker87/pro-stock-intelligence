import csv
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ingest_nse_auxiliary_history import import_corporate_zip, import_index_csv, parse_index_csv

class AuxiliaryNseIngestionTests(unittest.TestCase):
    def test_index_history_is_normalized_and_persisted_separately(self):
        payload = ("Index Name,Index Date,Open Index Value,High Index Value,Low Index Value,Closing Index Value\n"
                   "NIFTY 50,30-Oct-2026,25000,25100,24900,25050\n").encode()
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "index.csv"
            source.write_bytes(payload)
            out = Path(temp) / "indices"
            result = import_index_csv(source, "https://www.niftyindices.com/reports/historical-data", out)
            self.assertEqual(result["marketDataStatus"], "EOD")
            rows = json.loads((out / "2026-10-30.json").read_text())
            self.assertEqual(rows[0]["index"], "NIFTY 50")
            self.assertEqual(rows[0]["close"], "25050")

    def test_index_import_rejects_off_domain_and_bad_ohlc(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "bad.csv"
            source.write_text("Index,Date,Open,High,Low,Close\nNIFTY 50,2026-10-30,100,90,80,95\n")
            with self.assertRaisesRegex(ValueError, "official"):
                import_index_csv(source, "https://example.com/data.csv", Path(temp) / "out")
            with self.assertRaisesRegex(ValueError, "inconsistent"):
                parse_index_csv(source.read_bytes())

    def test_corporate_archive_retains_only_documented_event_files(self):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w") as archive:
            archive.writestr("An311026.txt", "sample announcement line\n")
            archive.writestr("Bc311026.csv", "sample,corporate,action\n")
            archive.writestr("Bm311026.txt", "sample board meeting line\n")
            archive.writestr("unrelated.txt", "ignore")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "nupr311026.zip"
            source.write_bytes(payload.getvalue())
            out = Path(temp) / "corporate"
            result = import_corporate_zip(source, "https://www.nseindia.com/all-reports", out)
            self.assertEqual(len(result["files"]), 3)
            self.assertTrue((out / "announcements/2026-10-31/An311026.txt").exists())
            self.assertTrue((out / "corporate_actions/2026-10-31/Bc311026.csv").exists())
            self.assertTrue((out / "board_meetings/2026-10-31/Bm311026.txt").exists())

    def test_corporate_archive_rejects_wrong_source_and_unknown_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "bad.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("other.txt", "not a documented NSE file")
            with self.assertRaisesRegex(ValueError, "official"):
                import_corporate_zip(source, "https://example.com/report.zip", Path(temp) / "out")
            with self.assertRaisesRegex(ValueError, "no documented"):
                import_corporate_zip(source, "https://www.nseindia.com/all-reports", Path(temp) / "out")

if __name__ == "__main__":
    unittest.main()
