import copy
import hashlib
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/coloros-port-8t/scripts"))
from verify_image_manifest import verify
from audit_artifacts import audit

class Checks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        data = b"image" * 1000
        (self.root / "system.img").write_bytes(data)
        self.manifest = dict(alignment=4096, group_limit=8192, partitions=[dict(partition="system", path="system.img", bytes=len(data), sha256=hashlib.sha256(data).hexdigest())])

    def test_valid_and_rounding(self):
        self.assertEqual(verify(self.manifest, self.root)["allocated_bytes"], 8192)

    def test_hash_and_length_failures(self):
        for field, value in [("sha256", "0" * 64), ("bytes", 1)]:
            with self.subTest(field=field):
                m = copy.deepcopy(self.manifest)
                m["partitions"][0][field] = value
                with self.assertRaises(ValueError): verify(m, self.root)

    def test_partition_scope_and_duplicates(self):
        for name in ["persist", "modemst1", "unknown"]:
            m = copy.deepcopy(self.manifest)
            m["partitions"][0]["partition"] = name
            with self.assertRaises(ValueError): verify(m, self.root)
        self.manifest["partitions"] *= 2
        with self.assertRaises(ValueError): verify(self.manifest, self.root)

    def test_path_escape(self):
        for path in ["../system.img", "C:/system.img", "/system.img", "..\\system.img"]:
            m = copy.deepcopy(self.manifest)
            m["partitions"][0]["path"] = path
            with self.assertRaises(ValueError): verify(m, self.root)

    def test_budget_and_alignment(self):
        for field, value in [("group_limit", 4096), ("alignment", 3), ("alignment", True)]:
            m = copy.deepcopy(self.manifest); m[field] = value
            with self.assertRaises(ValueError): verify(m, self.root)

    def test_sparse_rejected(self):
        data = bytes.fromhex("3aff26ed") + b"0" * 4996
        (self.root / "system.img").write_bytes(data)
        self.manifest["partitions"][0]["sha256"] = hashlib.sha256(data).hexdigest()
        with self.assertRaises(ValueError): verify(self.manifest, self.root)

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as other:
            target = Path(other) / "image"; target.write_bytes(b"test")
            link = self.root / "outside"
            try: link.symlink_to(target)
            except OSError: self.skipTest("symlink creation unavailable")
            self.manifest["partitions"][0]["path"] = "outside"
            with self.assertRaises(ValueError): verify(self.manifest, self.root)
            self.assertTrue(audit(self.root))

    def test_artifact_headers(self):
        (self.root / "bad.so").write_bytes(b"!<symlink>target")
        errors = audit(self.root)
        self.assertTrue(any("placeholder" in e for e in errors))
        self.assertTrue(any("not ELF" in e for e in errors))

    def test_apk_dex_and_duplicates(self):
        with zipfile.ZipFile(self.root / "app.apk", "w") as z:
            z.writestr("classes.dex", b"dex\n039\0" + b"0" * 120)
        self.assertEqual(audit(self.root, "039"), [])
        self.assertTrue(audit(self.root, "041"))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.root / "app.apk", "a") as z:
                z.writestr("classes.dex", b"invalid")
        errors = audit(self.root)
        self.assertTrue(any("duplicate" in e for e in errors))
        self.assertTrue(any("DEX header" in e for e in errors))

    def test_corrupt_zip(self):
        (self.root / "broken.apk").write_bytes(b"not a zip")
        self.assertTrue(audit(self.root))

if __name__ == "__main__":
    unittest.main()
