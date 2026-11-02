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
        end = source.index("\\n    )", start)
        block = source[start:end]
        import re
        symbols = re.findall(r'Stock\\("([A-Z0-9]+)"', block)
        self.assertEqual(len(symbols), 30)
        self.assertEqual(len(set(symbols)), 30)

    def test_screener_status_does_not_claim_subscription_authentication(self):
        source = NATIVE.read_text(encoding="utf-8")
        self.assertIn('.put("sessionAuthenticated", false)', source)
        self.assertIn("proves page access, not that subscription-only endpoints accepted the login", source)


if __name__ == "__main__":
    unittest.main()
