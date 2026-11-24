import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "app/src/main/assets/options-lab.html"
INDEX = ROOT / "app/src/main/assets/index.html"

class OptionsLabFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lab = LAB.read_text(encoding="utf-8")
        cls.index = INDEX.read_text(encoding="utf-8")

    def test_lab_is_integrated_as_a_separate_navigation_page(self):
        self.assertIn('data-page="options"', self.index)
        self.assertIn('id="optionsLabSection"', self.index)
        self.assertIn('src="options-lab.html"', self.index)
        self.assertIn("'options'", self.index)

    def test_calculator_has_required_inputs_and_greeks(self):
        for field in ("spot", "strike", "premium", "iv", "expiry", "rate", "dividend", "lot", "lots"):
            self.assertIn('id="' + field + '"', self.lab)
        for metric in ("delta", "gamma", "theta", "vega", "rho"):
            self.assertIn('id="' + metric + '"', self.lab)
        self.assertIn("function priceGreeks", self.lab)

    def test_calculator_does_not_claim_live_data_or_approve_trades(self):
        self.assertIn("NOT A LIVE OPTION CHAIN", self.lab)
        self.assertIn("NO TRADE — NOT VALIDATED", self.lab)
        self.assertIn("NOT CONNECTED", self.lab)
        self.assertIn("does not connect to NSE or broker feeds", self.lab)
        self.assertNotIn("FINAL DECISION: BUY", self.lab)

    def test_missing_inputs_are_not_replaced_with_defaults(self):
        self.assertIn("required.some(x=>x===null)", self.lab)
        self.assertIn("Missing inputs are not replaced with estimates.", self.lab)

    def test_no_order_execution_controls(self):
        self.assertNotIn("placeOrder", self.lab)
        self.assertNotIn("executeOrder", self.lab)
        self.assertNotIn("BUY CE", self.lab)
        self.assertNotIn("BUY PE", self.lab)

if __name__ == "__main__":
    unittest.main()
