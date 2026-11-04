import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
NATIVE = ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt"
GRADLE = ROOT / "app/build.gradle"
WORKFLOW = ROOT / ".github/workflows/build-apk.yml"

class V4100IntegratedRecoveryTests(unittest.TestCase):
    def test_v4200_version_is_aligned(self):
        gradle = GRADLE.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("versionName '42.02'", gradle)
        self.assertIn("versionCode 95", gradle)
        self.assertIn("PRO-STOCK-INTELLIGENCE-V42-02-debug", workflow)

    def test_screener_metrics_have_explicit_source_logic(self):
        source = NATIVE.read_text(encoding="utf-8")
        for token in (
            '"industry pe" to "industryPE"',
            '"piotroski score" to "piotroski"',
            '"peg ratio" to "peg"',
            '"pledged percentage" to "pledged"',
            "Industry P/E is provider-reported; peer median is not substituted",
            "Reported directly by Screener company-page ratios",
            "piotroskiCalculated",
            "piotroskiCalculatedMethod",
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

    def test_chartink_is_only_opened_as_an_external_user_driven_page(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("openChartinkScanner", html)
        self.assertIn("window.location.href='https://chartink.com/screener/'", html)
        self.assertNotIn("chartink.com/api", html)
        self.assertNotIn("fetchChartinkResults", html)

    def test_complete_stock_metric_matrix_is_rendered_with_missing_states_and_provenance(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        for token in ("Complete Stock Metrics Matrix", "industryPE", "piotroski", "pledged", "sales3y", "profit3y", "eps3y", "dma200", "RSI 14", "Source:", "Not returned by current source"):
            self.assertIn(token, html)
        self.assertIn("renderKeyMetricMatrix(d)", html)

    def test_no_fake_live_data_on_missing_gateway(self):
        source = NATIVE.read_text(encoding="utf-8")
        self.assertIn("Yahoo/Moneycontrol fallback is disabled", source)
        self.assertIn("No price or candle is fabricated", source)
        self.assertIn("No third-party fallback is used", source)

if __name__ == "__main__":
    unittest.main()
