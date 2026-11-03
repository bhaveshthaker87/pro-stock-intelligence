import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class BundledNseEodTests(unittest.TestCase):
    def test_build_bundles_only_validated_nse_eod_files(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("Bundle validated official NSE EOD history into Android assets", workflow)
        self.assertIn('target="app/src/main/assets/nse-eod"', workflow)
        self.assertIn('row.get("marketDataStatus") != "EOD"', workflow)
        self.assertIn("full-market rows retained", workflow)
        self.assertNotIn("tracked = {", workflow)
        self.assertIn("len(symbols) < 100", workflow)
        self.assertIn("Duplicate symbol", workflow)
        self.assertIn("Acquire official NSE EOD history when repository cache is empty", workflow)
        self.assertIn("Refusing to publish an APK that claims EOD history support", workflow)
        self.assertIn("if total == 0 or count_files(root) == 0", workflow)

    def test_android_provider_reads_only_official_eod_rows(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('appAssets.list("nse-eod")', source)
        self.assertIn('removePrefix("\\uFEFF")', source)
        self.assertIn('lowercase(Locale.ROOT)', source)
        self.assertIn('field("marketdatastatus")', source)
        self.assertIn('field("marketdatastatus").uppercase(Locale.ROOT) != "EOD"', source)
        self.assertIn('put("marketDataStatus", "EOD")', source)
        self.assertIn("Official NSE EOD closing price", source)
        self.assertIn("Not live, delayed or intraday", source)

    def test_gateway_validation_failure_does_not_downgrade_to_eod(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('if (gatewayConfigured()) {\n                            nseQuote(raw)\n                        } else {', source)
        self.assertIn('Configured provider gateway failed validation; price is unavailable. No fallback is used.', source)
        self.assertIn('Yahoo Finance unavailable', source)
        self.assertIn('eodQuote(raw)', source)


if __name__ == "__main__":
    unittest.main()
