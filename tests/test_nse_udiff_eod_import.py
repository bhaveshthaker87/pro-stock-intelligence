import io
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from convert_nse_udiff_bhavcopy import BhavcopyError, parse_bhavcopy_zip


HEADERS = "TradDt,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol,LastPric\n"
VALID = (
    "2026-10-29,TCS,EQ,3000.00,3050.00,2990.00,3030.00,123456,3032.00\n"
    "2026-10-29,TCS,BE,3000.00,3050.00,2990.00,3030.00,12,3032.00\n"
    "2026-10-29,INFY,EQ,1500.00,1510.00,1490.00,1505.00,98765,1506.00\n"
)


def zipped(csv_text):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("BhavCopy_NSE_CM_test.csv", csv_text)
    return out.getvalue()


class NseUdiffEodImportTests(unittest.TestCase):
    def test_parses_eq_only_and_labels_as_eod(self):
        rows = parse_bhavcopy_zip(zipped(HEADERS + VALID))
        self.assertEqual([r["symbol"] for r in rows], ["INFY", "TCS"])
        self.assertEqual(rows[1]["close"], "3030.00")
        self.assertEqual(rows[1]["volume"], "123456")
        self.assertEqual(rows[1]["date"], "2026-10-29")
        self.assertEqual(rows[1]["marketDataStatus"], "EOD")
        self.assertIn("NSE CM-UDiFF", rows[1]["source"])

    def test_rejects_wrong_or_old_format(self):
        with self.assertRaisesRegex(BhavcopyError, "missing UDiFF columns"):
            parse_bhavcopy_zip(zipped("SYMBOL,SERIES,CLOSE\nTCS,EQ,100\n"))

    def test_rejects_inconsistent_ohlc(self):
        bad = HEADERS + "2026-10-29,TCS,EQ,100,99,98,101,10,100\n"
        with self.assertRaisesRegex(BhavcopyError, "inconsistent OHLC"):
            parse_bhavcopy_zip(zipped(bad))

    def test_rejects_duplicate_symbol_date(self):
        row = "2026-10-29,TCS,EQ,100,102,98,101,10,100\n"
        with self.assertRaisesRegex(BhavcopyError, "duplicate EQ row"):
            parse_bhavcopy_zip(zipped(HEADERS + row + row))

    def test_rejects_invalid_price_and_empty_eq_file(self):
        bad = HEADERS + "2026-10-29,TCS,EQ,0,102,98,101,10,100\n"
        with self.assertRaisesRegex(BhavcopyError, "positive"):
            parse_bhavcopy_zip(zipped(bad))
        with self.assertRaisesRegex(BhavcopyError, "no valid EQ rows"):
            parse_bhavcopy_zip(zipped(HEADERS + "2026-10-29,TCS,BE,100,102,98,101,10,100\n"))

    def test_rejects_multiple_csvs_and_non_zip(self):
        with self.assertRaisesRegex(BhavcopyError, "exactly one CSV"):
            parse_bhavcopy_zip(zipped(HEADERS)[:-1] if False else self._multi_csv())
        with self.assertRaisesRegex(BhavcopyError, "cannot read"):
            parse_bhavcopy_zip(b"not a zip")

    @staticmethod
    def _multi_csv():
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as archive:
            archive.writestr("one.csv", HEADERS)
            archive.writestr("two.csv", HEADERS)
        return out.getvalue()


if __name__ == "__main__":
    unittest.main()
