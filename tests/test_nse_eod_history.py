import io
import json
import sys
import tempfile
import unittest
import zipfile
from datetime import date, datetime, timezone
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ingest_nse_eod_history import discover_report_url, ingest, probe_archive_for_latest_report

HEADERS = "TradDt,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol\n"
CSV = HEADERS + "2026-10-30,INFY,EQ,1500,1510,1490,1505,98765\n"

def zipped():
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("BhavCopy_NSE_CM_test.csv", CSV)
    return out.getvalue()

class NseEodHistoryTests(unittest.TestCase):
    def test_discovery_uses_only_official_https_udiff_links(self):
        html = '<a href="/api/reports/BhavCopy_NSE_CM_0_0_0_20261030_F_0000.csv.zip">CM-UDiFF Common Bhavcopy Final</a>'
        self.assertEqual(
            discover_report_url(html),
            "https://www.nseindia.in/api/reports/BhavCopy_NSE_CM_0_0_0_20261030_F_0000.csv.zip",
        )

    def test_discovery_rejects_missing_and_off_domain_links(self):
        with self.assertRaisesRegex(ValueError, "did not expose"):
            discover_report_url('<a href="https://example.com/BhavCopy_NSE_CM_0_0_0_20261030_F_0000.csv.zip">x</a>')
        with self.assertRaisesRegex(ValueError, "did not expose"):
            discover_report_url("<html>no report</html>")


    def test_discovery_reads_nse_data_attributes_and_official_archive_filename(self):
        html = '<div data-report-url="https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20261030_F_0000.csv.zip">CM-UDiFF</div>'
        self.assertEqual(
            discover_report_url(html),
            "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20261030_F_0000.csv.zip",
        )
        filename_only = '<span>BhavCopy_NSE_CM_0_0_0_20261030_F_0000.csv.zip</span>'
        self.assertEqual(
            discover_report_url(filename_only),
            "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20261030_F_0000.csv.zip",
        )

    def test_discovery_rejects_untrusted_data_attribute_url(self):
        html = '<div data-report-url="https://example.com/BhavCopy_NSE_CM_0_0_0_20261030_F_0000.csv.zip">CM-UDiFF</div>'
        with self.assertRaisesRegex(ValueError, "did not expose"):
            discover_report_url(html)

    def test_archive_probe_uses_latest_valid_official_trading_day(self):
        expected = "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20261030_F_0000.csv.zip"

        def fake_get(url, timeout=30):
            if url == expected:
                return zipped()
            raise ValueError("not a valid report")

        with patch("ingest_nse_eod_history._get", side_effect=fake_get):
            url, payload, rows = probe_archive_for_latest_report(date(2026, 10, 31), days=3)

        self.assertEqual(url, expected)
        self.assertTrue(payload.startswith(b"PK"))
        self.assertEqual(rows[0]["date"], "2026-10-30")

    def test_persists_idempotent_daily_history_and_manifest(self):
        html = '<a href="/BhavCopy_NSE_CM_0_0_0_20261030_F_0000.csv.zip">CM-UDiFF Common Bhavcopy Final</a>'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixed = datetime(2026, 10, 31, tzinfo=timezone.utc)
            first = ingest(root, html=html, zip_payload=zipped(), fetched_at=fixed)
            second = ingest(root, html=html, zip_payload=zipped(), fetched_at=fixed)
            self.assertEqual(first["tradingDate"], "2026-10-30")
            self.assertEqual(first["marketDataStatus"], "EOD")
            self.assertEqual(first["rowCount"], 1)
            self.assertEqual(second["sha256"], first["sha256"])
            self.assertTrue((root / "2026-10-30.csv").exists())
            manifest = json.loads((root / "index.json").read_text())
            self.assertEqual(len(manifest["tradingDates"]), 1)
            self.assertEqual(manifest["tradingDates"][0]["source"], "NSE CM-UDiFF Common Bhavcopy Final")

    def test_rejects_filename_and_row_date_mismatch(self):
        html = '<a href="/BhavCopy_NSE_CM_0_0_0_20261031_F_0000.csv.zip">CM-UDiFF Common Bhavcopy Final</a>'
        with tempfile.TemporaryDirectory() as temp, self.assertRaisesRegex(ValueError, "date mismatch"):
            ingest(Path(temp), html=html, zip_payload=zipped())

if __name__ == "__main__":
    unittest.main()
