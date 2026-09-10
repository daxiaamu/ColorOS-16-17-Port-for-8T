import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/coloros-port-8t/scripts"))
from donor_delta import snapshot, plan, read_json

class DonorDeltaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.tree = self.root / "tree"
        self.tree.mkdir()
        (self.tree / "framework.jar").write_bytes(b"old")
        (self.tree / "settings.apk").write_bytes(b"settings")
        self.old = snapshot(self.tree, "old")
        self.catalog = {"patches": [
            {"id": "framework", "state": "verified", "inputs": ["framework.jar"], "tests": ["boot"]},
            {"id": "settings", "state": "verified", "inputs": ["settings.apk"],
             "depends_on": ["framework"], "tests": ["ui"]}]}

    def test_identical_reuse_then_dependency_change(self):
        self.assertTrue(plan(self.old, self.old, self.catalog)["ready_for_candidate_reuse"])
        (self.tree / "framework.jar").write_bytes(b"new")
        result = plan(self.old, snapshot(self.tree, "new"), self.catalog)
        self.assertFalse(result["ready_for_candidate_reuse"])
        self.assertEqual(result["files"]["changed"], ["framework.jar"])
        self.assertEqual([x["decision"] for x in result["patches"]], ["review", "review"])
        self.assertIn("dependency-needs-review", result["patches"][1]["reasons"])

    def test_missing_addition_and_excluded_patch(self):
        (self.tree / "framework.jar").unlink()
        (self.tree / "new.apex").write_bytes(b"apex")
        result = plan(self.old, snapshot(self.tree, "new"), self.catalog)
        self.assertEqual(result["patches"][0]["decision"], "blocked")
        self.assertEqual(result["files"]["added"], ["new.apex"])
        for state in ["experimental", "reverted"]:
            c = copy.deepcopy(self.catalog); c["patches"][0]["state"] = state
            result = plan(self.old, self.old, c)
            self.assertEqual(result["patches"][0]["decision"], "excluded")
            self.assertEqual(result["patches"][1]["decision"], "review")

    def test_bad_baseline_cannot_reuse(self):
        old = copy.deepcopy(self.old); del old["entries"]["framework.jar"]
        self.assertEqual(plan(old, self.old, self.catalog)["patches"][0]["decision"], "blocked")

    def test_bad_catalog(self):
        for mutation in ["cycle", "unknown", "duplicate", "empty", "escape", "state"]:
            c = copy.deepcopy(self.catalog)
            if mutation == "cycle": c["patches"][0]["depends_on"] = ["settings"]
            if mutation == "unknown": c["patches"][0]["depends_on"] = ["missing"]
            if mutation == "duplicate": c["patches"].append(c["patches"][0])
            if mutation == "empty": c["patches"][0]["inputs"] = []
            if mutation == "escape": c["patches"][0]["inputs"] = ["../outside"]
            if mutation == "state": c["patches"][0]["state"] = "probably"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                plan(self.old, self.old, c)

    def test_directory_not_content_hash(self):
        (self.tree / "folder").mkdir()
        inv = snapshot(self.tree, "new")
        c = {"patches": [{"id": "folder", "state": "verified", "inputs": ["folder"]}]}
        with self.assertRaises(ValueError): plan(inv, inv, c)

    def test_duplicate_json_keys_rejected(self):
        p = self.root / "duplicate.json"; p.write_text('{"schema":1,"schema":2}')
        with self.assertRaises(ValueError): read_json(p)

    def test_cli_round_trip_and_no_overwrite(self):
        script = Path(__file__).resolve().parents[1] / "skills/coloros-port-8t/scripts/donor_delta.py"
        inv, cat, output = [self.root / n for n in ("inventory.json", "patches.json", "plan.json")]
        cat.write_text(json.dumps(self.catalog))
        subprocess.run([sys.executable, str(script), "snapshot", str(self.tree), "--label", "old",
                        "--output", str(inv)], check=True, capture_output=True)
        cmd = [sys.executable, str(script), "plan", str(inv), str(inv), "--patches", str(cat), "--output", str(output)]
        subprocess.run(cmd, check=True, capture_output=True)
        self.assertTrue(read_json(output)["ready_for_candidate_reuse"])
        before = output.read_bytes()
        self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
        self.assertEqual(output.read_bytes(), before)
        self.assertNotIn(str(self.tree), inv.read_text())

if __name__ == "__main__":
    unittest.main()
