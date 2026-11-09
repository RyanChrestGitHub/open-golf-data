import json
import tempfile
import unittest
from pathlib import Path

from open_golf_data.metric_view import MetricMapping, read_metric


class MetricViewTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "table.json"
        self.digest = "ab" * 32

    def table(self, field="Speed", unit="mph"):
        table = {
            "profile": "ogd-archive-table-v1",
            "source": {"label": "fictional", "revision": "invented", "sha256": self.digest,
                       "provenance": "fictional", "selection": "one metric"},
            "columns": [{"name": field, "unit": unit, "extra": "retained"}],
            "rows": [["0.00"], [None], [""], ["0.00"]],
        }
        self.path.write_text(json.dumps(table), encoding="utf-8")
        return self.path.read_bytes()

    def mapping(self, field="Speed", **changes):
        values = dict(key="ball_speed", source_sha256=self.digest, field=field,
                      provenance="fictional mapping r1", confidence="tentative")
        values.update(changes)
        return MetricMapping(**values)

    def read(self, mappings, key="ball_speed", digest=None):
        return read_metric(self.path, expected_source_sha256=digest or self.digest,
                           metric_key=key, mappings=mappings)

    def test_same_consumer_for_different_labels_and_units(self):
        for field, unit in [("Speed", "mph"), ("Velocity", "km/h")]:
            original = self.table(field, unit)
            result = self.read([self.mapping(field)])
            self.assertEqual(result["source_column"]["unit"], unit)
            self.assertEqual(result["source_column"]["extra"], "retained")
            self.assertEqual([row["raw_value"] for row in result["rows"]],
                             ["0.00", None, "", "0.00"])
            self.assertEqual([row["value_status"] for row in result["rows"]],
                             ["present", "missing", "blank", "present"])
            self.assertEqual(result["mapping"]["kind"], "unknown")
            self.assertEqual(result["mapping"]["confidence"], "tentative")
            self.assertEqual(self.path.read_bytes(), original)
            self.assertNotIn("captured_at", result)
            self.assertNotIn("source_event_id", result)

    def test_unknown_and_conflicting_units_stay_explicit(self):
        self.table(unit=None)
        self.assertEqual(self.read([self.mapping(expected_unit="mph")])["unit_status"],
                         "unknown")
        self.table(unit="sec")
        result = self.read([self.mapping(expected_unit="ms")])
        self.assertEqual(result["unit_status"], "conflicting")
        self.assertEqual(result["source_column"]["unit"], "sec")
        self.assertEqual(result["mapping"]["expected_unit"], "ms")
        self.assertEqual(result["rows"][0]["raw_value"], "0.00")

    def test_missing_ambiguous_and_wrong_source_mappings_fail(self):
        self.table()
        for mappings in [[], [self.mapping(), self.mapping()],
                         [self.mapping(source_sha256="cd" * 32)]]:
            with self.assertRaises(ValueError):
                self.read(mappings)
        with self.assertRaisesRegex(ValueError, "field"):
            self.read([self.mapping(field="absent")])
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            self.read([self.mapping()], digest="cd" * 32)

    def test_invalid_interpretation_metadata_fails(self):
        self.table()
        for changes in [dict(provenance=""), dict(confidence="certain"),
                        dict(kind="measured"), dict(expected_unit=""), dict(key="")]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.read([self.mapping(**changes)])

    def test_timing_numbers_are_never_rescaled(self):
        self.table("Duration [sec]", "sec")
        document = json.loads(self.path.read_text())
        document["rows"] = [["714"], ["0"], ["0.0"]]
        self.path.write_text(json.dumps(document))
        result = self.read([self.mapping("Duration [sec]", expected_unit="ms")])
        self.assertEqual([row["raw_value"] for row in result["rows"]], ["714", "0", "0.0"])
        self.assertEqual(result["unit_status"], "conflicting")
