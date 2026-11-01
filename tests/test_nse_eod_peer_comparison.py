from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NseEodPeerComparisonTests(unittest.TestCase):
    def test_peer_endpoint_uses_only_validated_bundled_nse_eod(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('"/api/peers" -> JSONObject().put("ok", true).put("data", peerComparison(s)).toString()', source)
        self.assertIn("private fun peerComparison(symbol: String): JSONObject", source)
        self.assertIn("readBundledNseEod(peer.symbol)", source)
        self.assertIn('put("marketDataType", "NSE_EOD")', source)
        self.assertIn('put("source", "NSE CM-UDiFF Common Bhavcopy Final")', source)

    def test_peer_endpoint_never_invents_missing_fundamentals(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        start = source.index("private fun peerComparison(symbol: String)")
        end = source.index("private fun htmlEntities", start)
        method = source[start:end]
        for field in ('"pe"', '"marketCap"', '"roce"', '"roe"', '"eps"'):
            self.assertIn(f".put({field}, JSONObject.NULL)", method)
        self.assertIn("fundamentals are not inferred", method)

    def test_dashboard_labels_eod_peer_rows_and_missing_fundamentals(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("Official NSE EOD peer closes", html)
        self.assertIn("Missing fundamentals remain unavailable", html)
        self.assertIn("marketDataType==='NSE_EOD'", html)


if __name__ == "__main__":
    unittest.main()
