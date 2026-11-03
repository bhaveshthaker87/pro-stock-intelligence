from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
INSTALLER = (ROOT / ".github/scripts/install-android-emulator-sdk.sh").read_text(encoding="utf-8")
EMULATOR = (ROOT / ".github/scripts/android-emulator-smoke.sh").read_text(encoding="utf-8")


class EmulatorInfrastructureTests(unittest.TestCase):
    def test_workflow_uses_explicit_emulator_scripts_not_action_auto_install(self):
        self.assertIn("install-android-emulator-sdk.sh", WORKFLOW)
        self.assertIn("android-emulator-smoke.sh", WORKFLOW)
        self.assertNotIn("reactivecircus/android-emulator-runner", WORKFLOW)

    def test_system_image_is_pinned_validated_and_retried_with_bounded_backoff(self):
        self.assertIn("system-images;android-34;google_apis;x86_64", INSTALLER)
        self.assertIn("for attempt in 1 2 3", INSTALLER)
        self.assertIn("sleep $((attempt * 20))", INSTALLER)
        self.assertIn("system.img", INSTALLER)
        self.assertIn("source.properties", INSTALLER)
        self.assertIn("package.xml", INSTALLER)
        self.assertIn('rm -rf "$IMAGE_DIR"', INSTALLER)

    def test_emulator_boot_and_adb_readiness_are_mandatory(self):
        self.assertIn("sys.boot_completed", EMULATOR)
        self.assertIn('status" == "device"', EMULATOR)
        self.assertIn("seq 1 120", EMULATOR)
        self.assertIn("exit 1", EMULATOR)

    def test_cleanup_is_idempotent_and_preserves_original_exit_code(self):
        self.assertIn("trap cleanup EXIT INT TERM", EMULATOR)
        self.assertIn("trap - EXIT INT TERM", EMULATOR)
        self.assertIn("local rc=$?", EMULATOR)
        self.assertIn("adb -s emulator-5554 emu kill", EMULATOR)

    def test_smoke_test_is_not_skipped_and_market_data_never_promoted_to_live(self):
        self.assertIn("android-smoke-test.sh", EMULATOR)
        self.assertIn("marketDataStatus", WORKFLOW)
        self.assertIn('{"REALTIME", "DELAYED", "EOD"}', WORKFLOW)

    def test_v42_version_and_optional_input_handling_remain(self):
        self.assertIn("versionCode='93' versionName='42.00'", WORKFLOW)
        self.assertIn("BUILD_SIGNED_RELEASE", EMULATOR)


if __name__ == "__main__":
    unittest.main()
