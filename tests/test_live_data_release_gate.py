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

    def test_yahoo_fallback_remains_disabled(self):
        self.assertIn("Authorized NSE/vendor gateway is not configured", self.main_activity)
        self.assertIn("The app does not substitute Yahoo-derived news", self.main_activity)
        self.assertIn("Screener provides fundamentals here; it is not used as a quote or candle provider.", self.main_activity)

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

    def test_nse_mcp_quote_has_enough_time_to_complete_streamable_http_handshake(self):
        # MCP quote uses initialize + initialized notification + tools/call.
        # The old 11-second shared deadline cancelled this sequence and returned blank prices.
        self.assertIn("TimeUnit.SECONDS.toNanos(48)", self.main_activity)
        self.assertIn("connection.connectTimeout = 5000", self.main_activity)
        self.assertIn("connection.readTimeout = 10000", self.main_activity)

    def test_dashboard_analysis_timeout_exceeds_native_mcp_budget(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("'/api/analyze':53000", html)
        self.assertIn("&mode=consolidated',53000)", html)

    def test_empty_events_are_not_proof_of_no_events(self):
        self.assertIn("Empty events means", self.provider_contract)
        self.assertIn("never treated as proof of no events", self.provider_contract)


if __name__ == "__main__":
    unittest.main()
