import pathlib
import unittest


class PremiumUiPolishTests(unittest.TestCase):
    def test_premium_responsive_layer_is_present(self):
        html = pathlib.Path("app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn('id="psi-premium-ui-polish"', html)
        self.assertIn("linear-gradient(105deg,#071b35", html)
        self.assertIn("@media(max-width:760px)", html)
        self.assertIn("@media(prefers-reduced-motion:reduce)", html)


    def test_simple_first_screen_and_advanced_toggle_are_present(self):
        html = pathlib.Path("app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("<title>Pro Stock Intelligence</title>", html)
        self.assertIn('id="search"', html)
        self.assertIn('id="analyze"', html)
        self.assertIn('id="psi-easy-first-screen"', html)
        self.assertIn("psi-easy-mode", html)
        self.assertIn("Show Advanced tools", html)
        self.assertIn("Back to Simple view", html)
        self.assertIn("id=\"providerStatus\"", html)

    def test_existing_dashboard_hooks_are_preserved(self):
        html = pathlib.Path("app/src/main/assets/index.html").read_text(encoding="utf-8")
        for required in ('id="search"', 'id="providerStatus"', "function verifyEngineVersion"):
            self.assertIn(required, html)


if __name__ == "__main__":
    unittest.main()
