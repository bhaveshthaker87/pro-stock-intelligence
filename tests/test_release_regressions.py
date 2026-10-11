from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]

class ReleaseRegressionTests(unittest.TestCase):
    def test_emulator_screenshot_does_not_write_to_sdcard(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("adb exec-out screencap -p > app/build/outputs/psi-emulator.png", workflow)
        self.assertNotIn("adb shell screencap -p /sdcard/psi-emulator.png", workflow)
        self.assertIn("89504e470d0a1a0a", workflow)

    def test_autocomplete_has_broad_provider_search_and_disclaimer(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("private fun equitySearch", source)
        self.assertIn("query1.finance.yahoo.com/v1/finance/search", source)
        self.assertIn('endsWith(".NS")', source)
        self.assertIn('endsWith(".BO")', source)
        self.assertIn("not a complete official NSE/BSE security master", source)

    def test_ui_and_native_engine_versions_match(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("V40.67 DATA QUALITY + RELEASE HARDENING", html)
        self.assertIn('"engine", "V40.67 DATA QUALITY + RELEASE HARDENING"', source)

    def test_quote_quality_does_not_infer_quote_time_from_response_time(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("UNVERIFIED_NO_PROVIDER_QUOTE_TIMESTAMP", source)
        self.assertIn("missing_not_inferred_from_response_time", source)
        self.assertIn("INVALID_FUTURE_TIMESTAMP", source)
        self.assertIn("quoteAgeSeconds", source)

    def test_exchange_label_does_not_always_claim_both_exchanges(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("q.exchange||'NSE/BSE availability not verified'", html)
        self.assertIn('raw.trim().uppercase(Locale.ROOT).endsWith(".BO") -> "BSE"', source)

if __name__ == "__main__":
    unittest.main()
