from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkflowInputSafetyTests(unittest.TestCase):
    def test_pull_request_emulator_script_normalizes_optional_dispatch_input(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        marker = "uses: reactivecircus/android-emulator-runner@v2"
        step = workflow[workflow.index(marker):]
        script = step[step.index("script: |"):step.index("\n\n      - name:", step.index("script: |"))]
        self.assertIn("inputs.build_signed_release || 'false'", script)
        self.assertIn('if [ "$BUILD_SIGNED_RELEASE" = "true" ]; then', script)
        self.assertNotIn('if [ "${{ inputs.build_signed_release }}" = "true" ]; then', script)
        # reactivecircus/android-emulator-runner executes each script line as a
        # separate shell command; the complete conditional must stay on one line.
        script_body = script.split("script: |", 1)[1].strip().splitlines()
        commands = [line.strip() for line in script_body if line.strip() and not line.lstrip().startswith("#")]
        self.assertEqual(len(commands), 1, "emulator script must be a single shell command")
        self.assertIn("; if [", commands[0])
        self.assertIn("; fi", commands[0])


if __name__ == "__main__":
    unittest.main()
