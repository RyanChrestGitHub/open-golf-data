"""Deterministic virtual device input; all values are fictional."""

import json
from pathlib import Path

from .ledger import Ledger
from .models import Observation


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "synthetic_session.json"


def run_fixture(ledger: Ledger, path: Path = FIXTURE_PATH) -> dict:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    if fixture.get("schema_version") != 1:
        raise ValueError("Unsupported fixture schema version")
    for installation in fixture["installations"]:
        ledger.register_installation(installation["id"], installation["mode"], installation["administrator"])
    for session in fixture["sessions"]:
        ledger.register_session(session["id"], session["installation_id"])
    for link in fixture["identity_links"]:
        ledger.link_participant(link["session_id"], link["participant_id"], link["golfer_id"], link["evidence"])
    inserted = 0
    for item in fixture["observations"]:
        # In a real adapter, raw_bytes would come from a native file/frame, NOT a reserialization.
        raw = json.dumps(item["native_payload"], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        obs = Observation(
            observation_id=item["id"], installation_id=item["installation_id"],
            session_id=item["session_id"], source=item["source"],
            source_event_id=item["source_event_id"], captured_at=item["captured_at"],
            raw_bytes=raw, source_participant_id=item.get("source_participant_id"),
            source_version=item.get("source_version", "unknown"), metrics=item.get("metrics", {}),
        )
        inserted += bool(ledger.ingest(obs))
    return {"source_fixture": str(path), "inserted": inserted, **ledger.counts()}
