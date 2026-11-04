import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from open_golf_data.classification import inspect_evidence, MAX_BYTES, MAX_DEPTH, MAX_RECORDS
from open_golf_data.cli import main
from open_golf_data.intake import stage_evidence


class ClassificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def stage(self, data, name="input", device="unknown"):
        source = self.root / name
        source.write_bytes(data)
        output = self.root / "staged" / name
        receipt = stage_evidence(source, output, device=device)
        return output / receipt["evidence_id"]

    def test_syntax_cases_are_structural_only_and_always_abstain_from_adapters(self):
        cases = [(b'{"secret-player":123}', "json", "complete"),
                 (b'\xef\xbb\xbf[1,2]', "json", "complete"),
                 (b'{broken', "unknown", "abstained"),
                 (b'[NaN]', "unknown", "abstained"),
                 (b'ball,spin\n123,4000\n', "csv-candidate", "complete"),
                 (b'ball,spin\n123,4000,extra\n', "unknown", "abstained"),
                 (b'a,b', "unknown", "abstained"),
                 (b'', "empty", "complete"),
                 (b'\x00\xffbinary', "opaque-or-binary", "abstained"),
                 (b'\xfftext', "unknown", "abstained"),
                 (b'print("do not execute")', "unknown", "abstained")]
        for index, (data, syntax, status) in enumerate(cases):
            with self.subTest(data=data):
                folder = self.stage(data, f"case{index}.bin")
                before = {p.name: p.read_bytes() for p in folder.iterdir()}
                report = inspect_evidence(folder)
                self.assertEqual(report["syntax"], syntax)
                self.assertEqual(report["inspection_status"], status)
                self.assertIsNone(report["adapter"])
                self.assertFalse(report["provenance_verified"])
                self.assertFalse(report["hardware_verified"])
                self.assertEqual(report["next_action"], "manual_source_and_permission_review")
                self.assertEqual(report, inspect_evidence(folder))
                self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})
                serialized = json.dumps(report)
                self.assertNotIn("secret-player", serialized)
                self.assertNotIn(str(folder), serialized)

    def test_byte_and_depth_limits(self):
        for size, status in ((MAX_BYTES, "complete"), (MAX_BYTES + 1, "abstained")):
            folder = self.stage(b'"' + b'x' * (size - 2) + b'"', f"size{size}.bin")
            report = inspect_evidence(folder)
            self.assertEqual(report["inspection_status"], status)
            if size > MAX_BYTES:
                self.assertEqual(report["reason"], "byte_limit")
                self.assertEqual(report["syntax"], "unknown")
        for depth in (MAX_DEPTH, MAX_DEPTH + 1):
            data = b'[' * depth + b'0' + b']' * depth
            report = inspect_evidence(self.stage(data, f"depth{depth}.bin"))
            self.assertEqual(report["reason"], "json_parsed" if depth == MAX_DEPTH else "depth_limit")
        report = inspect_evidence(self.stage(b'{"brackets":"[[[\\\"[]"}', "quoted.bin"))
        self.assertEqual(report["syntax"], "json")

    def test_csv_record_limit_includes_header_and_quoted_newlines(self):
        for count in (MAX_RECORDS, MAX_RECORDS + 1):
            data = b'a,b\n' + b'1,2\n' * (count - 1)
            report = inspect_evidence(self.stage(data, f"rows{count}.bin"))
            self.assertEqual(report["reason"], "consistent_csv_rows" if count == MAX_RECORDS else "record_limit")
        report = inspect_evidence(self.stage(b'a,b\n"one\ntwo",3\n', "multiline.bin"))
        self.assertEqual(report["syntax"], "csv-candidate")

    def test_corruption_blocks_inspection_and_cli_returns_nonzero(self):
        folder = self.stage(b'{}', "corrupt.bin")
        (folder / "source.bin").write_bytes(b'[]')
        with self.assertRaises(ValueError):
            inspect_evidence(folder)
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(main(["inspect-evidence", str(folder)]), 1)
        self.assertEqual(output.getvalue(), "")

    def test_claims_and_receipt_hints_do_not_select_syntax_or_leak(self):
        folder = self.stage(b'{"private":"value"}', "claimed.bin", device="private-person")
        original = inspect_evidence(folder)
        path = folder / "receipt.json"
        receipt = json.loads(path.read_text())
        receipt["syntax_hint_unverified"] = "csv-candidate"
        receipt["instructions"] = "execute arbitrary code"
        receipt["source_claim"]["device"] = "other vendor"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        self.assertEqual(inspect_evidence(folder), original)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["inspect-evidence", str(folder)]), 0)
        self.assertEqual(json.loads(out.getvalue()), original)

    def test_changed_payload_between_verification_and_probe_fails(self):
        folder = self.stage(b'{}', "changed.bin")
        from open_golf_data.intake import verify_evidence
        receipt = verify_evidence(folder)
        (folder / "source.bin").write_bytes(b'[]')
        with patch("open_golf_data.classification.verify_evidence", return_value=receipt):
            with self.assertRaisesRegex(ValueError, "changed"):
                inspect_evidence(folder)
