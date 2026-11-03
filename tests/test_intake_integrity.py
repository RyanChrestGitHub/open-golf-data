"""Offline evidence-byte integrity checks using only fictional inputs."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from open_golf_data.intake import stage_evidence


class IntakeIntegrityTests(unittest.TestCase):
    def test_corrupted_staged_bytes_rejected_without_repair_or_receipt_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "fictional.bin"
            source.write_bytes(b"\x00fictional original\xff")
            output = root / "evidence"
            receipt = stage_evidence(source, output)
            folder = output / receipt["evidence_id"]
            receipt_path = folder / "receipt.json"
            receipt_bytes = receipt_path.read_bytes()
            corrupted = b"fictional damaged bytes"
            (folder / "source.bin").write_bytes(corrupted)

            with self.assertRaisesRegex(ValueError, "Staged bytes differ from source digest"):
                stage_evidence(source, output)

            self.assertEqual((folder / "source.bin").read_bytes(), corrupted)
            self.assertEqual(receipt_path.read_bytes(), receipt_bytes)
            self.assertEqual(source.read_bytes(), b"\x00fictional original\xff")

    def test_source_changed_between_hash_and_copy_gets_no_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "fictional.bin"
            original = b"fictional bytes before copy"
            changed = b"fictional bytes changed during acquisition"
            source.write_bytes(original)
            output = root / "evidence"
            copyfile = shutil.copyfile

            def change_then_copy(src, dst):
                Path(src).write_bytes(changed)
                return copyfile(src, dst)

            with patch("open_golf_data.intake.shutil.copyfile", side_effect=change_then_copy):
                with self.assertRaisesRegex(ValueError, "Staged bytes differ from source digest"):
                    stage_evidence(source, output)

            evidence_id = "ev-" + hashlib.sha256(original).hexdigest()[:24]
            folder = output / evidence_id
            self.assertFalse((folder / "receipt.json").exists())
            # Failure retains the mismatched copy for investigation, not as accepted evidence.
            self.assertEqual((folder / "source.bin").read_bytes(), changed)
            source.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "Staged bytes differ from source digest"):
                stage_evidence(source, output)
            self.assertFalse((folder / "receipt.json").exists())
            self.assertEqual((folder / "source.bin").read_bytes(), changed)

    def test_empty_and_multiple_chunk_inputs_preserve_bytes_and_stable_receipts(self):
        for data in (b"", b"\x00\xfffictional\r\nbytes\x80"):
            with self.subTest(data=data), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "fictional.bin"
                source.write_bytes(data)
                output = root / "evidence"
                with patch("open_golf_data.intake.CHUNK_SIZE", 4):
                    first = stage_evidence(source, output)
                    folder = output / first["evidence_id"]
                    receipt_bytes = (folder / "receipt.json").read_bytes()
                    second = stage_evidence(source, output)
                self.assertEqual(first, second)
                self.assertEqual(first["content_sha256"], hashlib.sha256(data).hexdigest())
                self.assertEqual(first["size_bytes"], len(data))
                self.assertEqual((folder / "source.bin").read_bytes(), data)
                self.assertEqual((folder / "receipt.json").read_bytes(), receipt_bytes)
                self.assertEqual(json.loads(receipt_bytes), first)
                self.assertFalse(first["publication_approved"])
                self.assertFalse(first["real_hardware_verified"])
