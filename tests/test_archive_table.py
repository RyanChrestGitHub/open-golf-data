import json
import tempfile
import unittest
from pathlib import Path

from open_golf_data.archive_table import read_archive


class ArchiveTableTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "archive.json"
        self.digest = "ab" * 32

    def document(self, label, column, unit):
        return {
            "profile": "ogd-archive-table-v1",
            "source": {"label": label, "sha256": self.digest, "revision": "fictional",
                       "provenance": "invented test data", "selection": "selected columns"},
            "columns": [{"name": column, "unit": unit}, {"name": "extra", "unit": None}],
            "rows": [["0.00", None], ["", "unmapped"], ["0.00", None]],
        }

    def read(self, table, digest=None):
        self.path.write_text(json.dumps(table), encoding="utf-8")
        return read_archive(self.path, expected_source_sha256=digest or self.digest)

    def test_same_reader_preserves_two_lexical_projections_without_event_metadata(self):
        for label, column, unit in [("alpha", "A value", None), ("beta", "B value", "cm")]:
            with self.subTest(label=label):
                table = self.document(label, column, unit)
                self.assertEqual(self.read(table), table)

    def test_digest_and_ambiguous_shape_are_rejected(self):
        table = self.document("alpha", "value", None)
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            self.read(table, "cd" * 32)
        table["columns"][1]["name"] = "value"
        with self.assertRaisesRegex(ValueError, "duplicate archive column"):
            self.read(table)
        table["columns"][1]["name"] = "extra"
        table["rows"][0] = ["0"]
        with self.assertRaisesRegex(ValueError, "row shape"):
            self.read(table)

    def test_duplicate_json_keys_fail_closed(self):
        self.path.write_text('{"profile":"ogd-archive-table-v1","profile":"other"}',
                             encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate archive object key"):
            read_archive(self.path, expected_source_sha256=self.digest)
