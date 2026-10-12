"""Static release gates for the Android shell and market-data disclosure."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).parents[1]

class SecurityReleaseGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = ET.parse(ROOT / 'app/src/main/AndroidManifest.xml').getroot()
        cls.kotlin = (ROOT / 'app/src/main/java/com/prostock/intelligence/MainActivity.kt').read_text(encoding='utf-8')
        cls.provider_doc = (ROOT / 'PROVIDER_GATEWAY.md').read_text(encoding='utf-8')
        cls.workflow = (ROOT / '.github/workflows/build-apk.yml').read_text(encoding='utf-8')

    def test_cleartext_and_backup_disabled(self):
        app = self.manifest.find('application')
        self.assertEqual(app.attrib.get('{http://schemas.android.com/apk/res/android}usesCleartextTraffic'), 'false')
        self.assertEqual(app.attrib.get('{http://schemas.android.com/apk/res/android}allowBackup'), 'false')

    def test_webview_disables_file_and_content_access(self):
        self.assertIn('web.settings.allowFileAccess = false', self.kotlin)
        self.assertIn('web.settings.allowContentAccess = false', self.kotlin)
        self.assertIn('WebSettings.MIXED_CONTENT_NEVER_ALLOW', self.kotlin)
        self.assertIn('web.settings.safeBrowsingEnabled = true', self.kotlin)

    def test_webview_rejects_non_https_navigation_and_external_pages_open_outside(self):
        self.assertIn('if (!uri.scheme.equals("https", ignoreCase = true)) return false', self.kotlin)
        self.assertIn('if (uri.scheme.equals("https", ignoreCase = true))', self.kotlin)
        self.assertIn('Intent(Intent.ACTION_VIEW, uri)', self.kotlin)

    def test_network_calls_have_finite_timeouts(self):
        self.assertRegex(self.kotlin, r'connectTimeout\s*=\s*\d+')
        self.assertRegex(self.kotlin, r'readTimeout\s*=\s*\d+')

    def test_no_obvious_hardcoded_provider_secret_patterns(self):
        source_files = [ROOT / 'app/src/main/java/com/prostock/intelligence/MainActivity.kt', ROOT / 'app/src/main/assets/index.html']
        patterns = [r'(?i)api[_-]?key\s*[:=]\s*["\'][A-Za-z0-9_-]{16,}',
                    r'(?i)client_secret\s*[:=]\s*["\'][^"\']{12,}',
                    r'(?i)Bearer\s+[A-Za-z0-9._-]{24,}']
        for path in source_files:
            text = path.read_text(encoding='utf-8')
            for pattern in patterns:
                self.assertIsNone(re.search(pattern, text), f'Potential embedded secret pattern in {path.name}: {pattern}')

    def test_provider_gateway_explicitly_requires_real_vendor_and_samples(self):
        self.assertIn('does **not** have a licensed vendor configured', self.provider_doc)
        self.assertIn('Real sanitized fixtures from the provider pass validation', self.provider_doc)
        self.assertIn('No provider API key is present in source or built APK', self.provider_doc)

    def test_ci_build_lint_emulator_and_screenshot_checks_are_mandatory(self):
        for required in ('gradle :app:assembleDebug', 'gradle :app:lintDebug',
                         'reactivecircus/android-emulator-runner@v2',
                         'adb exec-out screencap -p > app/build/outputs/psi-emulator.png',
                         'test -s app/build/outputs/psi-emulator.png'):
            self.assertIn(required, self.workflow)

if __name__ == '__main__':
    unittest.main()
