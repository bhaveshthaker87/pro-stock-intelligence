import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
NATIVE = ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt"
GRADLE = ROOT / "app/build.gradle"
WORKFLOW = ROOT / ".github/workflows/build-apk.yml"

class V4092IntegratedRecoveryTests(unittest.TestCase):
    def test_version_is_aligned(self):
        gradle = GRADLE.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("versionName '40.92'", gradle)
        self.assertIn("PRO-STOCK-INTELLIGENCE-V40-92-debug", workflow)

    def test_screener_metrics_have_explicit_source_logic(self):
        source = NATIVE.read_text(encoding="utf-8")
        for token in (
            '"industry pe" to "industryPE"',
            '"piotroski score" to "piotroski"',
            '"peg ratio" to "peg"',
            '"pledged percentage" to "pledged"',
            "Median P/E of valid peers in the Screener peer table",
            "Reported directly by Screener company-page ratios",
            "P/E divided by 3-year EPS CAGR (%)",
            "UNAVAILABLE_REQUIRES_POSITIVE_EPS_CAGR",
        ):
            self.assertIn(token, source)

    def test_quote_and_chart_paths_do_not_call_yahoo_adapter(self):
        source = NATIVE.read_text(encoding="utf-8")
        combined = source[source.index("private fun combined("):source.index("private fun fundamentalsWithDownstox")]
        history = source[source.index("private fun historyData("):source.index("Read only validated NSE EQ bhavcopy")]
        api_quote = source[source.index('"/api/quote", "/api/fast"'):source.index('"/api/history"')]
        self.assertNotIn("yahooChart(", combined)
        self.assertNotIn("yahooChart(", history)
        self.assertNotIn("yahooChart(", api_quote)
        self.assertIn("OFFICIAL_NSE_EOD_UNAVAILABLE", source)
        self.assertIn("NSE_EOD_HISTORY_NOT_BUNDLED", history)

    def test_no_fake_live_data_on_missing_gateway(self):
        source = NATIVE.read_text(encoding="utf-8")
        self.assertIn("Yahoo/Moneycontrol fallback is disabled", source)
        self.assertIn("No price or candle is fabricated", source)
        self.assertIn("No third-party fallback is used", source)

if __name__ == "__main__":
    unittest.main()
