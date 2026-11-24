"""V43.00 regression tests for NSE gateway time and range integrity."""

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "market-data-gateway/app.py").read_text(encoding="utf-8")
KOTLIN = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def function_source(name):
    node = next(n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    return ast.get_source_segment(SOURCE, node)


class GatewayIntegrityTests(unittest.TestCase):
    def test_nse_wall_clock_is_interpreted_as_ist_then_converted_to_utc(self):
        body = function_source("_nse_time")
        self.assertIn('ZoneInfo("Asia/Kolkata")', body)
        self.assertIn("astimezone(timezone.utc)", body)
        self.assertNotIn("replace(tzinfo=timezone.utc)", body)

    def test_all_frontend_chart_ranges_are_explicitly_supported(self):
        body = function_source("android_history")
        for timeframe in ("1d", "1w", "1mo", "3mo", "6mo", "ytd", "1y", "3y", "5y", "all"):
            with self.subTest(timeframe=timeframe):
                self.assertIn(f'"{timeframe}"', body)
        self.assertIn("Unsupported history range", body)
        self.assertNotIn('.get(range, 366)', body)
        self.assertIn('"rangeRequested": range', body)

    def test_historical_daily_bars_use_india_local_date_boundary(self):
        body = function_source("android_history")
        self.assertIn('replace(tzinfo=ZoneInfo("Asia/Kolkata"))', body)

    def test_android_rejects_gateway_response_for_a_different_requested_range(self):
        self.assertIn('if (returnedRange != range) throw IOException("History provider range mismatch', KOTLIN)
        helper_start = KOTLIN.index("private fun filterEodRowsForRange")
        helper_end = KOTLIN.index("\\n    /** Read only validated NSE EQ bhavcopy", helper_start)
        helper = KOTLIN[helper_start:helper_end]
        for timeframe in ("1d", "1w", "1mo", "3mo", "6mo", "ytd", "1y", "3y", "5y", "all"):
            with self.subTest(timeframe=timeframe):
                self.assertIn(f'"{timeframe}"', helper)
        self.assertIn('if (range == "1d") selected.takeLast(1)', helper)
        self.assertIn('range !in setOf("1d", "1w", "1mo", "3mo")', KOTLIN)

    def test_missing_event_announcement_time_is_not_replaced_with_current_time(self):
        body = function_source("_as_iso_time")
        events = function_source("_event_rows")
        dividends = function_source("android_dividends")
        self.assertIn("fallback: str | None = None", body)
        self.assertIn('"announcedAt": announced', events)
        self.assertIn('_as_iso_time(_first(row, "broadcastDate", "announcementDate"))', dividends)
        self.assertNotIn("now)", events)
        self.assertNotIn('now)', dividends)


if __name__ == "__main__":
    unittest.main()
