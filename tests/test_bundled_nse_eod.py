import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class BundledNseEodTests(unittest.TestCase):
    def test_build_bundles_only_validated_nse_eod_files(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("Bundle validated official NSE EOD history into Android assets", workflow)
        self.assertIn('target="app/src/main/assets/nse-eod"', workflow)
        self.assertIn('row.get("marketDataStatus") != "EOD"', workflow)
        self.assertIn("tracked-symbol NSE EOD rows", workflow)

    def test_android_provider_reads_only_official_eod_rows(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('appAssets.list("nse-eod")', source)
        self.assertIn('field("marketDataStatus") != "EOD"', source)
        self.assertIn('put("marketDataStatus", "EOD")', source)
        self.assertIn("Official NSE EOD closing price", source)
        self.assertIn("Not live, delayed or intraday", source)

    def test_gateway_validation_failure_does_not_downgrade_to_eod(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('if (gatewayConfigured()) nseQuote(raw) else eodQuote(raw)', source)
        self.assertIn('if (gatewayConfigured()) nseQuote(raw) else eodQuote(raw)', source)


if __name__ == "__main__":
    unittest.main()
