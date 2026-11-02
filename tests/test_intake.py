import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from open_golf_data.intake import stage_evidence


class IntakeTests(unittest.TestCase):
    def test_unknown_binary_is_losslessly_staged_without_vendor_assumptions(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            src = root / "mystery.dat"
            data = b"\x00\xff\x12hidden\x00binary"
            src.write_bytes(data)
            receipt = stage_evidence(src, root / "lab-evidence")
            self.assertEqual(receipt["content_sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(receipt["source_claim"]["device"], "unknown")
            self.assertFalse(receipt["publication_approved"])
            self.assertFalse(receipt["real_hardware_verified"])
            self.assertEqual((root / "lab-evidence" / receipt["evidence_id"] / "source.bin").read_bytes(), data)

    def test_repeat_is_idempotent_conflicting_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            src = root / "session.csv"
            src.write_text("ball,spin\n123,4000\n")
            target = root / "lab-evidence"
            a = stage_evidence(src, target, device="ExampleMonitor")
            b = stage_evidence(src, target, device="ExampleMonitor")
            self.assertEqual(a, b)
            self.assertEqual(a["syntax_hint_unverified"], "csv-candidate")
            with self.assertRaises(ValueError):
                stage_evidence(src, target, device="A different claim")
            self.assertEqual(json.loads((target / a["evidence_id"] / "receipt.json").read_text())["source_claim"]["device"], "ExampleMonitor")

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            src = root / "source"
            src.write_text("test")
            alias = root / "alias"
            alias.symlink_to(src)
            with self.assertRaises(ValueError):
                stage_evidence(alias, root / "lab-evidence")


if __name__ == "__main__":
    unittest.main()
