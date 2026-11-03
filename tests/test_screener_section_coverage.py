from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt"
HTML = ROOT / "app/src/main/assets/index.html"


class ScreenerSectionCoverageTests(unittest.TestCase):
    def test_all_financial_sections_are_parsed_from_explicit_screener_containers(self):
        source = NATIVE.read_text(encoding="utf-8")
        for section_id in ("profit-loss", "quarters", "shareholding", "balance-sheet",
                           "cash-flow", "ratios", "peers"):
            self.assertIn(f'sectionTableRows(html, "{section_id}")', source)

    def test_extended_tables_are_returned_in_normalized_fundamentals_payload(self):
        source = NATIVE.read_text(encoding="utf-8")
        for key in ("balanceSheet", "cashFlow", "ratios", "peerComparison"):
            self.assertIn(f'f.put("{key}", jsonRows(', source)

    def test_section_coverage_distinguishes_missing_sections(self):
        source = NATIVE.read_text(encoding="utf-8")
        for key in ("profitLoss", "quarterly", "balanceSheet", "cashFlow",
                    "shareholding", "financialRatios", "peerComparison"):
            self.assertIn(f'.put("{key}",', source)
        self.assertIn('.put("sectionCoverage", sectionCoverage)', source)

    def test_core_coverage_exposes_per_field_status_and_percent(self):
        source = NATIVE.read_text(encoding="utf-8")
        self.assertIn('.put("fields", fields)', source)
        self.assertIn('.put("sections", sections)', source)
        self.assertIn('.put("coveragePercent"', source)

    def test_dashboard_counts_sections_and_fields_separately(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("coverage.sections||f.sectionCoverage", html)
        self.assertIn("coverage.fields||{}", html)
        self.assertIn("financial sections", html)
        self.assertIn("core fields", html)

    def test_dashboard_does_not_derive_pe_from_price_and_unverified_eps(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertNotIn("Number(f.price)/Number(f.eps)", html)
        self.assertIn("validated TTM profit", html)

    def test_native_provider_uses_shared_fundamentals_cache(self):
        source = NATIVE.read_text(encoding="utf-8")
        self.assertIn("ConcurrentHashMap<String, CachedFundamentals>", source)
        self.assertIn("fundamentalsCacheTtlMs", source)
        self.assertIn('put("cacheStatus", "HIT")', source)
        self.assertIn('put("cacheStatus", "BYPASS_ON_ERROR")', source)

    def test_backend_publishes_single_versioned_normalized_dataset(self):
        source = NATIVE.read_text(encoding="utf-8")
        for key in ("normalizedData", "schemaVersion", "market", "fundamentals",
                    "financials", "coverage", "generatedAtEpochMs"):
            self.assertIn(f'put("{key}"', source)

    def test_dashboard_consumes_normalized_dataset_for_all_financial_views(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("d?.normalizedData||d||{}", html)
        self.assertIn("canonical.market||d.market||{}", html)
        self.assertIn("canonical.financials||{}", html)

    def test_validation_universe_contains_30_unique_nse_symbols(self):
        source = NATIVE.read_text(encoding="utf-8")
        start = source.index("private val stocks = listOf(")
        end = source.index("\n    )", start)
        block = source[start:end]
        import re
        symbols = re.findall(r'Stock\("([A-Z0-9]+)"', block)
        self.assertEqual(len(symbols), 30)
        self.assertEqual(len(set(symbols)), 30)

    def test_screener_status_does_not_claim_subscription_authentication(self):
        source = NATIVE.read_text(encoding="utf-8")
        self.assertIn('.put("sessionAuthenticated", false)', source)
        self.assertIn("Subscription-only access is not proven by this public-page probe", source)
        self.assertIn('.put("subscriptionAccessVerified", false)', source)


    def test_piotroski_prefers_screener_reported_score_and_calculates_only_as_fallback(self):
        source = NATIVE.read_text(encoding="utf-8")
        self.assertIn('"piotroski score" to "piotroski"', source)
        self.assertIn('if (!f.has("piotroski") && piotroskiInputs.all { it != null })', source)
        self.assertIn('Reported directly by Screener company-page ratios', source)
        self.assertIn("UNAVAILABLE_MISSING_REQUIRED_ANNUAL_INPUTS", source)
        self.assertIn("Calculated from Screener annual financial statements", source)
        self.assertIn("shareCapitalNow <= shareCapitalPrev", source)

    def test_peg_uses_eps_growth_only_and_never_profit_growth(self):
        source = NATIVE.read_text(encoding="utf-8")
        self.assertIn('"peg ratio" to "peg"', source)
        self.assertIn('f.optDouble("eps3y"', source)
        self.assertIn("P/E divided by 3-year EPS CAGR (%)", source)
        self.assertNotIn('f.optDouble("profit3y"', source)
        self.assertIn("UNAVAILABLE_REQUIRES_POSITIVE_EPS_CAGR", source)

    def test_four_screener_top_ratio_fields_are_mapped_and_industry_pe_has_peer_fallback(self):
        source = NATIVE.read_text(encoding="utf-8")
        for token in ('"industry pe" to "industryPE"', '"piotroski score" to "piotroski"',
                      '"peg ratio" to "peg"', '"pledged percentage" to "pledged"'):
            self.assertIn(token, source)
        self.assertIn("Median P/E of valid peers in the Screener peer table", source)
        self.assertIn('label.contains("pledg") || label.contains("encumber")', source)

    def test_v4111_pledge_parser_accepts_pledged_and_encumbered_labels(self):
        source = NATIVE.read_text(encoding="utf-8")
        self.assertIn('label.contains("pledg") || label.contains("encumber")', source)

    def test_v4110_industry_pe_uses_peer_median_and_chart_ticks_are_mobile_safe(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("Median P/E of valid peers in the Screener peer table", source)
        self.assertIn("peerPes.size >= 3", source)
        self.assertIn("Peer-table reporting period not labelled", source)
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("Math.min(5,Math.floor(plotW/170))", html)
        self.assertIn("c.textAlign=k===0?'left':k===ticks?'right':'center'", html)
        self.assertIn("Period not supplied", html)
        self.assertIn("Official NSE EOD supplies closing prices only", html)

if __name__ == "__main__":
    unittest.main()
