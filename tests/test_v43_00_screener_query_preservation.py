"""V43.00 regression tests for preserving built-in Screener query definitions."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = json.loads((ROOT / "docs/V43.00_SCREENER_QUERY_INVENTORY.json").read_text(encoding="utf-8"))
KOTLIN = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
HTML = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")


class ScreenerQueryPreservationTests(unittest.TestCase):
    def test_inventory_contains_seven_unique_builtin_queries(self):
        queries = INVENTORY["builtInQueries"]
        ids = [item["id"] for item in queries]
        self.assertEqual(len(queries), 7)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, INVENTORY["frontendOrder"])

    def test_exact_query_definitions_match_kotlin_source(self):
        for item in INVENTORY["builtInQueries"]:
            with self.subTest(query_id=item["id"]):
                self.assertIn(f'.put("id", "{item["id"]}")', KOTLIN)
                self.assertIn(f'.put("name", "{item["name"]}")', KOTLIN)
                self.assertIn(f'.put("query", "{item["query"]}")', KOTLIN)

    def test_frontend_order_and_storage_keys_are_preserved(self):
        order = ",".join(f"'{query_id}'" for query_id in INVENTORY["frontendOrder"])
        self.assertIn(f"const QUERY_CARD_ORDER=[{order}]", HTML)
        self.assertIn(INVENTORY["localStorageKeys"]["userQueryOverrides"], HTML)
        self.assertIn(INVENTORY["localStorageKeys"]["scanHistory"], HTML)

    def test_query_overrides_are_applied_without_mutating_defaults(self):
        self.assertRegex(HTML, r"const merged=\(items\|\|\)\.map\(x=>\(\{\.\.\.x,\.\.\.\(overrides\[x\.id\]\|\|\{\}\)\}\)\)")
        self.assertIn("function qWrite(key,value)", HTML)


if __name__ == "__main__":
    unittest.main()
