import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class OptionsSignalsReadOnlyTests(unittest.TestCase):
    def test_options_signals_workspace_is_loaded_by_dashboard(self):
        html=(ROOT/"app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("options-signals.js",html)
    def test_options_module_fails_closed_without_broker_authentication(self):
        source=(ROOT/"app/src/main/assets/options-signals.js").read_text(encoding="utf-8")
        self.assertIn("API KEY NOT GENERATED",source)
        self.assertIn("NO AUTHORIZED LIVE FEED",source)
        self.assertIn("NO SIGNAL",source)
        self.assertIn("liveSignalsEnabled:false",source)
    def test_options_module_is_read_only_and_has_no_order_actions(self):
        source=(ROOT/"app/src/main/assets/options-signals.js").read_text(encoding="utf-8")
        self.assertIn("orderPlacementEnabled:false",source)
        self.assertIn("order placement disabled",source.lower())
        self.assertNotIn("/api/orders",source)
        self.assertNotIn("placeOrder",source)
    def test_both_brokers_and_static_ip_confirmation_are_visible(self):
        source=(ROOT/"app/src/main/assets/options-signals.js").read_text(encoding="utf-8")
        self.assertIn("m.Stock",source)
        self.assertIn("Motilal Oswal",source)
        self.assertIn("broker confirmation pending",source)
if __name__=="__main__": unittest.main()
