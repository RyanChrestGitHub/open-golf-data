import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from open_golf_data.cli import main
from open_golf_data.intake import stage_evidence, verify_evidence


class EvidenceVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        source = self.root / "fictional.bin"
        source.write_bytes(b"\x00fictional source\xff")
        self.receipt = stage_evidence(source, self.root / "evidence")
        self.folder = self.root / "evidence" / self.receipt["evidence_id"]
        source.unlink()  # Verification must not require the original acquisition path.

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.folder.iterdir()}

    def write_receipt(self, receipt):
        (self.folder / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")

    def test_verify_and_cli_are_read_only_and_do_not_promote_claims(self):
        self.receipt["future_field"] = {"claim": "unverified"}
        self.write_receipt(self.receipt)
        before = self.snapshot()
        with patch("open_golf_data.intake.CHUNK_SIZE", 4):
            self.assertEqual(verify_evidence(self.folder), self.receipt)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(main(["verify-evidence", str(self.folder)]), 0)
        report = json.loads(stream.getvalue())
        self.assertTrue(report["integrity_matches_receipt"])
        self.assertFalse(report["provenance_verified"])
        self.assertEqual(self.snapshot(), before)

    def test_corrupt_bytes_fail_without_rewriting_anything(self):
        (self.folder / "source.bin").write_bytes(b"changed")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "digest or size"):
            verify_evidence(self.folder)
        self.assertEqual(self.snapshot(), before)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertNotEqual(main(["verify-evidence", str(self.folder)]), 0)

    def test_invalid_receipts_fail_without_rewriting(self):
        cases = [None, [], {}, {**self.receipt, "schema_version": 2},
                 {**self.receipt, "schema_version": True},
                 {**self.receipt, "schema_version": 1.0},
                 {**self.receipt, "size_bytes": True},
                 {**self.receipt, "size_bytes": -1},
                 {**self.receipt, "content_sha256": "../source.bin"},
                 {**self.receipt, "evidence_id": "ev-wrong"},
                 {**self.receipt, "source_claim": []},
                 {**self.receipt, "source_claim": {"device": "unknown"}},
                 {**self.receipt, "publication_approved": True},
                 {**self.receipt, "real_hardware_verified": True},
                 {**self.receipt, "status": "physically_tested"}]
        for receipt in cases:
            with self.subTest(receipt=receipt):
                self.write_receipt(receipt)
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    verify_evidence(self.folder)
                self.assertEqual(self.snapshot(), before)

    def test_missing_or_malformed_receipt_and_missing_payload_fail(self):
        receipt_path = self.folder / "receipt.json"
        receipt_path.write_text("{", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_evidence(self.folder)
        receipt_path.unlink()
        with self.assertRaises(ValueError):
            verify_evidence(self.folder)
        self.write_receipt(self.receipt)
        (self.folder / "source.bin").unlink()
        with self.assertRaises(ValueError):
            verify_evidence(self.folder)

    def test_duplicate_json_fields_and_symlink_paths_are_rejected(self):
        receipt_path = self.folder / "receipt.json"
        text = json.dumps(self.receipt)
        receipt_path.write_text('{"schema_version":2,' + text[1:], encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate receipt field"):
            verify_evidence(self.folder)
        self.write_receipt(self.receipt)
        before = self.snapshot()
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaisesRegex(ValueError, "Symlink evidence paths"):
                verify_evidence(self.folder)
        self.assertEqual(self.snapshot(), before)

    def test_size_mismatch_and_empty_payload(self):
        self.write_receipt({**self.receipt, "size_bytes": 0})
        with self.assertRaisesRegex(ValueError, "digest or size"):
            verify_evidence(self.folder)
        empty = self.root / "empty"
        empty.write_bytes(b"")
        receipt = stage_evidence(empty, self.root / "evidence")
        self.assertEqual(verify_evidence(self.root / "evidence" / receipt["evidence_id"]), receipt)
