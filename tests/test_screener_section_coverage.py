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


if __name__ == "__main__":
    unittest.main()
