import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class LiveDataReleaseGateTests(unittest.TestCase):
    """Guard against silently presenting fallback/reference data as live market data."""

    @classmethod
    def setUpClass(cls):
        cls.main_activity = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        cls.workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        cls.provider_contract = (ROOT / "PROVIDER_GATEWAY.md").read_text(encoding="utf-8")

    def test_yahoo_finance_is_an_explicit_timestamp_checked_price_fallback(self):
        self.assertIn("private fun yahooChart(raw: String", self.main_activity)
        self.assertIn("https://query1.finance.yahoo.com/v8/finance/chart/", self.main_activity)
        self.assertIn('put("provider", "Yahoo Finance")', self.main_activity)
        self.assertIn('put("marketDataStatus", "UNVERIFIED_SNAPSHOT")', self.main_activity)
        self.assertIn("older than five days", self.main_activity)
        self.assertIn('if (gatewayConfigured()) {', self.main_activity)
        self.assertIn('try { yahooChart(raw, "1y") }', self.main_activity)
        self.assertIn("Screener provides fundamentals here; it is not used as a quote or candle provider.", self.main_activity)

    def test_yahoo_fallback_never_claims_exchange_certified_realtime(self):
        self.assertIn('put("isExchangeCertifiedRealtime", false)', self.main_activity)
        self.assertIn("not exchange-certified real-time", self.main_activity)
        self.assertIn("Yahoo Finance daily OHLCV", self.main_activity)

    def test_missing_gateway_is_explicitly_not_verified(self):
        self.assertIn("LIVE DATA NOT VERIFIED", self.workflow)
        self.assertIn("No live-feed pass is claimed", self.workflow)

    def test_release_can_require_provider_gateway(self):
        self.assertIn("REQUIRE_LIVE_PROVIDER_GATEWAY", self.workflow)
        self.assertIn("require_live_data", self.workflow)
        self.assertIn("exit 1", self.workflow)

    def test_contract_requires_source_timestamp_and_status(self):
        self.assertIn("source", self.provider_contract)
        self.assertIn("asOf", self.provider_contract)
        self.assertIn("marketDataStatus", self.provider_contract)
        self.assertIn("REALTIME", self.provider_contract)
        self.assertIn("DELAYED", self.provider_contract)
        self.assertIn("EOD", self.provider_contract)

    def test_empty_events_are_not_proof_of_no_events(self):
        self.assertIn("Empty events means", self.provider_contract)
        self.assertIn("never treated as proof of no events", self.provider_contract)


if __name__ == "__main__":
    unittest.main()
