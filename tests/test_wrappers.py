from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WrapperStateTests(unittest.TestCase):
    def run_wrapper(self, relative, action):
        return subprocess.run(
            ["python3", relative, action],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )

    def test_rapp_map_is_privacy_blocked_not_green(self):
        checked = self.run_wrapper(
            "tools/wrappers/rapp_map_offline.py", "--check"
        )
        self.assertEqual(checked.returncode, 0)
        self.assertIn("state=blocked-private-boundary", checked.stdout)
        run = self.run_wrapper("tools/wrappers/rapp_map_offline.py", "--run")
        self.assertEqual(run.returncode, 3)

    def test_rapp_spine_is_privacy_blocked_not_green(self):
        checked = self.run_wrapper(
            "tools/wrappers/rapp_spine_offline.py", "--check"
        )
        self.assertEqual(checked.returncode, 0)
        self.assertIn("state=blocked-private-boundary", checked.stdout)
        run = self.run_wrapper("tools/wrappers/rapp_spine_offline.py", "--run")
        self.assertEqual(run.returncode, 3)

    def test_ultracode_overlay_check_remains_ready(self):
        checked = self.run_wrapper(
            "tools/wrappers/ultracode_local_rdw.py", "--check"
        )
        self.assertEqual(checked.returncode, 0)
        self.assertIn("resolves RDW", checked.stdout)


if __name__ == "__main__":
    unittest.main()
