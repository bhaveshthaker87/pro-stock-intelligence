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
        self.assertIn('field("marketDataStatus").uppercase(Locale.ROOT) != "EOD"', source)
        self.assertIn('put("marketDataStatus", "EOD")', source)
        self.assertIn("Official NSE EOD closing price", source)
        self.assertIn("Not live, delayed or intraday", source)

    def test_gateway_validation_failure_uses_delayed_then_eod_fallback(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        start = source.index("private fun marketQuote(raw: String)")
        end = source.index("private fun nseQuote(raw: String)", start)
        pipeline = source[start:end]
        self.assertLess(pipeline.index("nseQuote(raw)"), pipeline.index("nseMcpQuote(raw)"))
        self.assertLess(pipeline.index("nseMcpQuote(raw)"), pipeline.index("eodQuote(raw)"))
        self.assertIn('put("fallbackLevel", "NSE_MCP_DELAYED")', pipeline)
        self.assertIn('put("fallbackLevel", "BUNDLED_NSE_EOD")', pipeline)
        self.assertIn("No verified NSE quote available", pipeline)


if __name__ == "__main__":
    unittest.main()
