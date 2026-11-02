"""Append-only observation ledger with conservative, explicit participant mapping.

This is a *local trusted-operator* library, NOT an authenticated cloud service.
No network endpoints are exposed; passing player_id here is not authentication.
"""

import base64
import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import Observation


class SourceConflictError(ValueError):
    """A source event ID or observation ID is being reused with different data."""


class IdentityConflictError(ValueError):
    """A participant is already explicitly mapped to another golfer."""


class Ledger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS installations (
                id TEXT PRIMARY KEY,
                mode TEXT NOT NULL CHECK(mode IN ('home','facility')),
                administrator TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                installation_id TEXT NOT NULL REFERENCES installations(id)
            );
            CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY,
                installation_id TEXT NOT NULL REFERENCES installations(id),
                session_id TEXT NOT NULL REFERENCES sessions(id),
                source TEXT NOT NULL,
                source_event_id TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                source_participant_id TEXT,
                source_version TEXT NOT NULL,
                raw_bytes BLOB NOT NULL,
                source_sha256 TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                ingested_at TEXT NOT NULL,
                UNIQUE (installation_id, session_id, source, source_event_id)
            );
            CREATE TABLE IF NOT EXISTS participant_links (
                session_id TEXT NOT NULL REFERENCES sessions(id),
                source_participant_id TEXT NOT NULL,
                golfer_id TEXT NOT NULL,
                evidence TEXT NOT NULL,
                PRIMARY KEY (session_id, source_participant_id)
            );
        """)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Ledger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def register_installation(self, installation_id: str, mode: str, administrator: str) -> None:
        if mode not in {"home", "facility"} or not installation_id or not administrator:
            raise ValueError("Installation requires ID, home/facility mode, and administrator")
        row = self.conn.execute("SELECT * FROM installations WHERE id=?", (installation_id,)).fetchone()
        if row is not None:
            if (row["mode"], row["administrator"]) != (mode, administrator):
                raise SourceConflictError("Existing installation has different ownership/mode")
            return
        with self.conn:
            self.conn.execute("INSERT INTO installations VALUES (?,?,?)", (installation_id, mode, administrator))

    def register_session(self, session_id: str, installation_id: str) -> None:
        if not session_id:
            raise ValueError("Session ID is required")
        row = self.conn.execute("SELECT installation_id FROM sessions WHERE id=?", (session_id,)).fetchone()
        if row is not None:
            if row["installation_id"] != installation_id:
                raise SourceConflictError("Session already belongs to another installation")
            return
        with self.conn:
            self.conn.execute("INSERT INTO sessions VALUES (?,?)", (session_id, installation_id))

    def link_participant(self, session_id: str, source_participant_id: str, golfer_id: str, evidence: str) -> None:
        if not all((session_id, source_participant_id, golfer_id, evidence)):
            raise ValueError("Identity link requires participant, golfer and explicit evidence")
        row = self.conn.execute(
            "SELECT * FROM participant_links WHERE session_id=? AND source_participant_id=?",
            (session_id, source_participant_id),
        ).fetchone()
        if row is not None:
            if (row["golfer_id"], row["evidence"]) != (golfer_id, evidence):
                raise IdentityConflictError("Existing participant link cannot be silently reassigned")
            return
        with self.conn:
            self.conn.execute(
                "INSERT INTO participant_links VALUES (?,?,?,?)",
                (session_id, source_participant_id, golfer_id, evidence),
            )

    def ingest(self, observation: Observation) -> bool:
        """Store exact source bytes. Return False for exact idempotent replay.

        The source event key must not be reused for changed content or metrics.
        """
        observation.validate()
        session = self.conn.execute("SELECT installation_id FROM sessions WHERE id=?", (observation.session_id,)).fetchone()
        if session is None or session["installation_id"] != observation.installation_id:
            raise ValueError("Observation installation/session association is invalid")
        sha = hashlib.sha256(observation.raw_bytes).hexdigest()
        metrics_json = json.dumps(observation.metrics, sort_keys=True, separators=(",", ":"), allow_nan=False)
        existing = self.conn.execute(
            """SELECT * FROM observations WHERE id=? OR
               (installation_id=? AND session_id=? AND source=? AND source_event_id=?)""",
            (observation.observation_id, observation.installation_id, observation.session_id,
             observation.source, observation.source_event_id),
        ).fetchall()
        if existing:
            if len(existing) != 1:
                raise SourceConflictError("Observation ID conflicts with source event key")
            row = existing[0]
            match = (
                row["id"] == observation.observation_id
                and row["installation_id"] == observation.installation_id
                and row["session_id"] == observation.session_id
                and row["source"] == observation.source
                and row["source_event_id"] == observation.source_event_id
                and row["captured_at"] == observation.captured_at
                and row["source_participant_id"] == observation.source_participant_id
                and row["source_version"] == observation.source_version
                and row["raw_bytes"] == observation.raw_bytes
                and row["source_sha256"] == sha
                and row["metrics_json"] == metrics_json
            )
            if match:
                return False
            raise SourceConflictError("Source event changed; rejecting silent overwrite")
        with self.conn:
            self.conn.execute(
                """INSERT INTO observations (
                   id, installation_id, session_id, source, source_event_id,
                   captured_at, source_participant_id, source_version, raw_bytes,
                   source_sha256, metrics_json, ingested_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (observation.observation_id, observation.installation_id,
                 observation.session_id, observation.source, observation.source_event_id,
                 observation.captured_at, observation.source_participant_id,
                 observation.source_version, observation.raw_bytes, sha, metrics_json,
                 datetime.now(timezone.utc).isoformat()),
            )
        return True

    def counts(self) -> dict:
        total = self.conn.execute("SELECT count(*) FROM observations").fetchone()[0]
        attributable = self.conn.execute("""
            SELECT count(*) FROM observations AS o JOIN participant_links AS p
            ON p.session_id=o.session_id AND p.source_participant_id=o.source_participant_id
        """).fetchone()[0]
        return {"observations": total, "attributed": attributable, "unclaimed": total-attributable}

    def observations_for_golfer(self, golfer_id: str) -> list[dict]:
        """Local, trusted-context export. A cloud API MUST authenticate the caller.

        Records without evidence-backed participant links are excluded.
        """
        if not golfer_id:
            raise ValueError("Golfer ID required")
        rows = self.conn.execute("""
            SELECT o.*, p.golfer_id, p.evidence FROM observations AS o
            JOIN participant_links AS p
              ON o.session_id=p.session_id
             AND o.source_participant_id=p.source_participant_id
            WHERE p.golfer_id=? ORDER BY o.captured_at, o.id
        """, (golfer_id,)).fetchall()
        records = []
        for row in rows:
            raw = bytes(row["raw_bytes"])
            if hashlib.sha256(raw).hexdigest() != row["source_sha256"]:
                raise SourceConflictError("Stored source payload failed SHA-256 integrity check")
            try:
                native_json = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                native_json = None
            records.append({
                "observation_id": row["id"],
                "session_id": row["session_id"],
                "installation_id": row["installation_id"],
                "source": row["source"],
                "source_event_id": row["source_event_id"],
                "source_participant_id": row["source_participant_id"],
                "source_version": row["source_version"],
                "captured_at": row["captured_at"],
                "source_sha256": row["source_sha256"],
                "source_raw_base64": base64.b64encode(raw).decode("ascii"),
                "source_payload_json": native_json,
                "interpreted_metrics": json.loads(row["metrics_json"]),
                "attribution_evidence": row["evidence"],
            })
        return records

    def export_golfer(self, golfer_id: str, destination: str | Path) -> Path:
        """Export only linked records. Must be called by a trusted local operator."""
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        records = self.observations_for_golfer(golfer_id)
        if destination.suffix == ".json":
            destination.write_text(json.dumps({
                "schema": "open-golf-data/portable-history/v0",
                "golfer_id": golfer_id,
                "observations": records,
            }, indent=2) + "\n", encoding="utf-8")
        elif destination.suffix == ".csv":
            fields = [
                "observation_id", "session_id", "installation_id", "source",
                "source_event_id", "source_participant_id", "source_version",
                "captured_at", "source_sha256", "source_raw_base64",
                "source_payload_json", "interpreted_metrics", "attribution_evidence"
            ]
            with destination.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for record in records:
                    flat = dict(record)
                    for key in ("source_payload_json", "interpreted_metrics"):
                        flat[key] = json.dumps(flat[key], sort_keys=True, separators=(",", ":"))
                    writer.writerow(flat)
        else:
            raise ValueError("Use a .json or .csv export filename")
        return destination
