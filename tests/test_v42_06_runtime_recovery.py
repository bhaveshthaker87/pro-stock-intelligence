import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")

class V4206RuntimeRecoveryTests(unittest.TestCase):
    def test_default_stock_analysis_starts_on_first_launch(self):
        self.assertIn('id="psi-v42-06-runtime-recovery"', HTML)
        self.assertIn("window.__PSI_AUTO_ANALYSIS_STARTED=true", HTML)
        self.assertIn("search.value='INFY'", HTML)
        self.assertIn("analyze.click()", HTML)

    def test_unhandled_async_errors_are_visible(self):
        self.assertIn("addEventListener('unhandledrejection'", HTML)
        self.assertIn("Dashboard error:", HTML)

    def test_easy_mode_css_does_not_contain_literal_newline_escapes(self):
        match = re.search(r'<style id="psi-easy-first-screen">(.*?)</style>', HTML, re.S)
        self.assertIsNotNone(match)
        self.assertNotIn(r"\n/* Keep the requested fundamentals matrix", match.group(1))
        self.assertIn("body.psi-easy-mode .factor{display:block!important}", match.group(1))

    def test_data_sources_controls_are_registered_once(self):
        self.assertEqual(HTML.count("$('dataSourcesBtn')?.addEventListener('click'"), 1)
        self.assertEqual(HTML.count("$('dataSourcesClose')?.addEventListener('click'"), 1)

    def test_screener_queries_and_fundamental_parser_are_not_replaced(self):
        self.assertIn("/api/screen/querytext", HTML)
        self.assertIn("/api/screener/live", HTML)

    def test_long_research_sections_are_collapsed_by_default(self):
        self.assertIn("psi-v42-06-professional-compact-ui", HTML)
        self.assertIn("psiAiMoreBtn", HTML)
        self.assertIn("psiFactorMoreBtn", HTML)
        self.assertIn("psi-ai-compact", HTML)
        self.assertIn("psi-factor-compact", HTML)

    def test_combined_analysis_recovers_nse_eod_close_after_quote_deadline(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        combined = source[source.index("private fun combined("):source.index("private fun historyData")]
        self.assertIn("BUNDLED_NSE_EOD_AFTER_PROVIDER_TIMEOUT", combined)
        self.assertIn("val eod = eodQuote(s)", combined)
        self.assertIn("VALIDATED_OFFICIAL_NSE_EOD", combined)

if __name__ == "__main__":
    unittest.main()
