from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class V4100ReleaseGateTests(unittest.TestCase):
    def test_gateway_secret_fallback_is_used_for_debug_build(self):
        y=(ROOT/".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("PROVIDER_GATEWAY_BASE_URL_SECRET: ${{ secrets.PROVIDER_GATEWAY_BASE_URL }}",y)
        self.assertIn('if [ -z "$PROVIDER_GATEWAY_BASE_URL" ]; then PROVIDER_GATEWAY_BASE_URL="${PROVIDER_GATEWAY_BASE_URL_SECRET:-}"; fi',y)
        self.assertIn('-PproviderGatewayBaseUrl="${PROVIDER_GATEWAY_BASE_URL:-}"',y)

    def test_signed_release_requires_complete_360_metric_screener_audit(self):
        y=(ROOT/".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("data/screener/30-stock-reconciliation.csv",y)
        self.assertIn("--require-complete",y)
        self.assertIn("Signed production release requires the populated 30-stock Screener reconciliation CSV",y)

    def test_release_apk_signature_metadata_and_install_are_verified(self):
        y=(ROOT/".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        smoke=(ROOT/".github/scripts/android-smoke-test.sh").read_text(encoding="utf-8")
        self.assertIn('apksigner verify --verbose --print-certs "$APK"',y)
        self.assertIn('aapt dump badging "$APK"',y)
        self.assertIn("versionCode='92' versionName='41.00'",y)
        self.assertIn('PSI_SMOKE_APK="app/build/outputs/apk/release/app-release.apk"',y)
        self.assertIn('APK="${PSI_SMOKE_APK:-app/build/outputs/apk/debug/app-debug.apk}"',smoke)

if __name__=="__main__": unittest.main()
