import contextlib
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from open_golf_data.cli import main
from open_golf_data.csv_projection import project_csv
from open_golf_data.intake import stage_evidence, verify_evidence
from open_golf_data.metric_view import MetricMapping, read_metric


class CsvProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.spec = dict(encoding="utf-8", delimiter=",", header_record=2,
                         first_record=3, last_record=5,
                         columns=[dict(name="Speed", unit="mph"), dict(name="Note", unit=None)],
                         label="fictional", revision="invented-v1",
                         provenance="Fictional test", selection="Records 3-5; all fields")
        self.config = self.root / "config.json"
        self.config.write_text(json.dumps(self.spec))
        self.source = self.root / "input.csv"
        self.source.write_bytes(b'metadata\r\nSpeed,Note\r\n0.00,"comma, and\r\nnewline"\r\n,""\r\n0.00,"comma, and\r\nnewline"\r\n')
        self.receipt = stage_evidence(self.source, self.root / "staging")
        self.evidence = self.root / "staging" / self.receipt["evidence_id"]
        self.output = self.root / "archive.json"

    def test_pipeline_preserves_exact_cells_and_inputs(self):
        before = {p: p.read_bytes() for p in [self.source, self.evidence / "source.bin",
                                             self.evidence / "receipt.json", self.config]}
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(main(["project-csv", str(self.evidence), "--config", str(self.config),
                                   "--output", str(self.output)]), 0)
        digest = verify_evidence(self.evidence)["content_sha256"]
        self.assertEqual(json.loads(stdout.getvalue())["source_sha256"], digest)
        mapping = MetricMapping("ball_speed", digest, "Speed", "fictional", "tentative", expected_unit="km/h")
        view = read_metric(self.output, expected_source_sha256=digest, metric_key="ball_speed", mappings=[mapping])
        self.assertEqual([r["raw_value"] for r in view["rows"]], ["0.00", "", "0.00"])
        self.assertEqual(view["unit_status"], "conflicting")
        note = MetricMapping("note", digest, "Note", "fictional", "unknown")
        view = read_metric(self.output, expected_source_sha256=digest, metric_key="note", mappings=[note])
        self.assertEqual(view["unit_status"], "unknown")
        self.assertEqual([r["raw_value"] for r in view["rows"]], ["comma, and\r\nnewline", "", "comma, and\r\nnewline"])
        self.assertEqual(json.loads(self.output.read_text())["projection"]["first_record"], 3)
        for p, data in before.items():
            self.assertEqual(p.read_bytes(), data)

    def test_invalid_configuration_does_not_publish(self):
        changes = [{"encoding": "utf-16"}, {"delimiter": ";"}, {"header_record": True},
                   {"header_record": 0}, {"first_record": 2}, {"last_record": 25},
                   {"last_record": 99}, {"columns": []}, {"label": ""},
                   {"columns": [{"name": "Absent", "unit": None}]},
                   {"columns": [{"name": "Speed", "unit": 3}]},
                   {"columns": [dict(name="Speed", unit=None)] * 2}, {"extra": "unsupported"}]
        for change in changes:
            with self.subTest(change=change):
                spec = copy.deepcopy(self.spec)
                spec.update(change)
                self.config.write_text(json.dumps(spec))
                with self.assertRaises((ValueError, TypeError)):
                    project_csv(self.evidence, self.config, self.output)
                self.assertFalse(self.output.exists())

    def test_invalid_csv_and_integrity_do_not_publish(self):
        cases = [b'\xff', b'\xef\xbb\xbfSpeed,Note\n1,2\n', b'Speed;Note\n1;2\n',
                 b'Speed,Speed\n1,2\n', b'Speed,\n1,2\n', b'Speed,Note\n1\n',
                 b'Speed,Note\n1,2,3\n', b'Speed,Note\n"unterminated,2',
                 b'Speed,Note\n1"bad,2\n', b'Speed,Note\n"x"bad,2\n',
                 b'Speed,Note\n1,\0\n']
        for n, payload in enumerate(cases):
            with self.subTest(n=n):
                self.source.write_bytes(payload)
                receipt = stage_evidence(self.source, self.root / "other")
                evidence = self.root / "other" / receipt["evidence_id"]
                spec = dict(self.spec, header_record=1, first_record=2, last_record=2)
                self.config.write_text(json.dumps(spec))
                with self.assertRaises((ValueError, UnicodeError, csv.Error)):
                    project_csv(evidence, self.config, self.output)
                self.assertFalse(self.output.exists())
        (self.evidence / "source.bin").write_bytes(b'changed')
        with self.assertRaises(ValueError):
            project_csv(self.evidence, self.config, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_output_and_write_failure_leave_no_partial_archive(self):
        self.output.write_text("keep")
        with self.assertRaises(ValueError):
            project_csv(self.evidence, self.config, self.output)
        self.assertEqual(self.output.read_text(), "keep")
        self.output.unlink()
        with patch("open_golf_data.csv_projection.os.link", side_effect=OSError("failure")):
            with self.assertRaises(OSError):
                project_csv(self.evidence, self.config, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["config.json", "input.csv", "staging"])

    def test_changed_snapshot_and_receipt_fail_before_publication(self):
        def change_after_verification(folder):
            result = verify_evidence(folder)
            (folder / "source.bin").write_bytes(b"different")
            return result

        with patch("open_golf_data.csv_projection.verify_evidence", side_effect=change_after_verification):
            with self.assertRaises(ValueError):
                project_csv(self.evidence, self.config, self.output)
        self.assertFalse(self.output.exists())

    def test_escaped_quotes_and_limit_boundary(self):
        self.source.write_bytes(b'Speed,Note\n' + b'00,"a""b"\n' * 20)
        receipt = stage_evidence(self.source, self.root / "twenty")
        spec = dict(self.spec, header_record=1, first_record=2, last_record=21)
        self.config.write_text(json.dumps(spec))
        project_csv(self.root / "twenty" / receipt["evidence_id"], self.config, self.output)
        self.assertEqual(json.loads(self.output.read_text())["rows"], [["00", 'a"b']] * 20)

    def test_fields_above_python_default_limit_within_byte_bound(self):
        long_text = "x" * 140000
        self.source.write_bytes(("Speed,Note\n0.00," + long_text + "\n").encode())
        receipt = stage_evidence(self.source, self.root / "long")
        evidence = self.root / "long" / receipt["evidence_id"]
        previous_limit = csv.field_size_limit()
        for columns in (self.spec["columns"], [dict(name="Speed", unit="mph")]):
            spec = dict(self.spec, header_record=1, first_record=2, last_record=2, columns=columns)
            self.config.write_text(json.dumps(spec))
            project_csv(evidence, self.config, self.output)
            rows = json.loads(self.output.read_text())["rows"]
            self.assertEqual(rows, [["0.00", long_text]] if len(columns) == 2 else [["0.00"]])
            self.assertEqual(csv.field_size_limit(), previous_limit)
            self.output.unlink()

    def test_cli_failure_has_no_partial_stdout_or_archive(self):
        self.config.write_text('{"encoding":"utf-8","encoding":"utf-16"}')
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(main(["project-csv", str(self.evidence), "--config", str(self.config),
                                   "--output", str(self.output)]), 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertFalse(self.output.exists())
