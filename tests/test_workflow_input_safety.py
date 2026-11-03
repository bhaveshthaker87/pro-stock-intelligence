from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkflowInputSafetyTests(unittest.TestCase):
    def test_pull_request_emulator_script_normalizes_optional_dispatch_input(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        emulator = (ROOT / ".github/scripts/android-emulator-smoke.sh").read_text(encoding="utf-8")
        self.assertIn("BUILD_SIGNED_RELEASE: ${{ inputs.build_signed_release || 'false' }}", workflow)
        self.assertIn('BUILD_SIGNED_RELEASE="${BUILD_SIGNED_RELEASE:-false}"', emulator)
        self.assertIn('if [[ "$BUILD_SIGNED_RELEASE" == "true" ]]; then', emulator)
        self.assertIn('PSI_SMOKE_APK="app/build/outputs/apk/release/app-release.apk"', emulator)
        self.assertIn("bash .github/scripts/android-smoke-test.sh", emulator)


if __name__ == "__main__":
    unittest.main()
