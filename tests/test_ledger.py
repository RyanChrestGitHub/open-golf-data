"""Contract and regression tests for hard information boundaries."""

import base64
import csv
import json
import tempfile
import unittest
from pathlib import Path

from open_golf_data.fixture import run_fixture, FIXTURE_PATH
from open_golf_data.ledger import Ledger, IdentityConflictError, SourceConflictError
from open_golf_data.models import Observation


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "events.sqlite"
        self.ledger = Ledger(self.db)
        self.addCleanup(self.ledger.close)

    def test_fictional_fixture_reconciles_without_guessing_owner(self):
        result = run_fixture(self.ledger)
        self.assertEqual(result["observations"], 5)
        self.assertEqual(result["attributed"], 4)
        self.assertEqual(result["unclaimed"], 1)
        self.assertEqual(result["inserted"], 5)
        self.assertEqual(run_fixture(self.ledger)["inserted"], 0)

    def test_golfer_records_follow_identity_links_across_installations(self):
        run_fixture(self.ledger)
        a = self.ledger.observations_for_golfer("golfer-001")
        b = self.ledger.observations_for_golfer("golfer-002")
        self.assertEqual({r["observation_id"] for r in a}, {"obs-monitor-A1", "obs-sim-A1", "obs-home-A1"})
        self.assertEqual({r["observation_id"] for r in b}, {"obs-monitor-B1"})
        self.assertTrue({r["installation_id"] for r in a} == {"facility-lab-001", "home-lab-001"})
        self.assertNotIn("obs-monitor-unclaimed", [r["observation_id"] for r in a+b])

    def test_source_fields_preserved_exactly_even_when_not_normalized(self):
        run_fixture(self.ledger)
        a = next(r for r in self.ledger.observations_for_golfer("golfer-001") if r["observation_id"] == "obs-monitor-A1")
        self.assertEqual(a["source_payload_json"]["NewUndocumentedField"], 27)
        self.assertIsNone(a["source_payload_json"]["ClubFace"])
        self.assertIsNone(a["interpreted_metrics"]["club_face"]["value"])
        self.assertEqual(a["interpreted_metrics"]["club_face"]["kind"], "unknown")
        original = self.ledger.conn.execute("SELECT raw_bytes FROM observations WHERE id='obs-monitor-A1'").fetchone()[0]
        self.assertEqual(base64.b64decode(a["source_raw_base64"]), original)

    def test_simulated_and_device_observations_not_silently_merged(self):
        run_fixture(self.ledger)
        records = self.ledger.observations_for_golfer("golfer-001")
        monitor = next(r for r in records if r["observation_id"] == "obs-monitor-A1")
        sim = next(r for r in records if r["observation_id"] == "obs-sim-A1")
        self.assertEqual(monitor["interpreted_metrics"]["ball_speed"]["kind"], "device_reported")
        self.assertEqual(sim["interpreted_metrics"]["carry"]["kind"], "simulated")
        self.assertNotIn("carry", monitor["interpreted_metrics"])
        self.assertNotIn("ball_speed", sim["interpreted_metrics"])

    def test_source_id_collision_must_fail_closed(self):
        run_fixture(self.ledger)
        item = self.ledger.conn.execute("SELECT * FROM observations WHERE id='obs-monitor-A1'").fetchone()
        changed = Observation(
            observation_id=item["id"], installation_id=item["installation_id"],
            session_id=item["session_id"], source=item["source"],
            source_event_id=item["source_event_id"], captured_at=item["captured_at"],
            raw_bytes=b'{"BallVelocity":999}', source_participant_id=item["source_participant_id"],
            source_version=item["source_version"], metrics={"ball_speed":{"value":999,"unit":"mph","kind":"device_reported"}},
        )
        with self.assertRaises(SourceConflictError):
            self.ledger.ingest(changed)
        self.assertEqual(self.ledger.counts()["observations"], 5)

    def test_identity_cannot_silently_reassign(self):
        run_fixture(self.ledger)
        with self.assertRaises(IdentityConflictError):
            self.ledger.link_participant("facility-session-001", "gspro-player-A", "golfer-002", "fictional-participant-confirmation")
        self.assertEqual(len(self.ledger.observations_for_golfer("golfer-002")), 1)

    def test_export_contains_recoverable_original_bytes(self):
        run_fixture(self.ledger)
        j = self.ledger.export_golfer("golfer-001", Path(self.tmp.name) / "golfer.json")
        c = self.ledger.export_golfer("golfer-001", Path(self.tmp.name) / "golfer.csv")
        jdata = json.loads(j.read_text())
        self.assertEqual(len(jdata["observations"]), 3)
        with c.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 3)
        self.assertIn(b'NewUndocumentedField', base64.b64decode(rows[0]["source_raw_base64"]))
        self.assertNotIn("obs-monitor-B1", c.read_text())

    def test_corrupted_stored_payload_fails_export(self):
        run_fixture(self.ledger)
        with self.ledger.conn:
            self.ledger.conn.execute("UPDATE observations SET raw_bytes=? WHERE id=?", (b'{"tampered":true}', 'obs-monitor-A1'))
        with self.assertRaisesRegex(SourceConflictError, "SHA-256 integrity check"):
            self.ledger.observations_for_golfer("golfer-001")

    def test_reopen_and_replay_does_not_duplicate(self):
        run_fixture(self.ledger)
        self.ledger.close()
        self.ledger = Ledger(self.db)
        self.addCleanup(self.ledger.close)
        self.assertEqual(run_fixture(self.ledger)["inserted"], 0)
        self.assertEqual(self.ledger.counts()["observations"], 5)

    def test_reject_naive_timestamp_and_invalid_metric(self):
        base = dict(observation_id="x", installation_id="i", session_id="s", source="mock",
                    source_event_id="m-1", raw_bytes=b'{}')
        with self.assertRaises(ValueError):
            Observation(**base, captured_at="2026-11-02T13:00:00").validate()
        with self.assertRaises(ValueError):
            Observation(**base, captured_at="2026-11-02T13:00:00Z",
                        metrics={"club_path": {"value": None, "unit": "deg", "kind": "device_reported"}}).validate()

    def test_failure_is_explicit_on_unknown_fixture_version(self):
        fixture = json.loads(FIXTURE_PATH.read_text())
        fixture["schema_version"] = 99
        path = Path(self.tmp.name) / "broken.json"
        path.write_text(json.dumps(fixture))
        with self.assertRaisesRegex(ValueError, "Unsupported fixture schema"):
            run_fixture(self.ledger, path)
        self.assertEqual(self.ledger.counts()["observations"], 0)


if __name__ == "__main__":
    unittest.main()
