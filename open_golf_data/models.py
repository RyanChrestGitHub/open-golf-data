"""Minimal, intentionally vendor-neutral input contracts for the initial lab.

An Observation represents a SOURCE EVENT, not a physical golf shot. The
source payload is byte-preserving; derived metric interpretations are separate.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

SUPPORTED_KINDS = frozenset({
    "device_reported", "vendor_estimated", "simulated", "calculated", "unknown"
})


def validate_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid ISO 8601 timestamp: {value!r}") from exc
    if parsed.utcoffset() is None:
        raise ValueError("Timestamps must carry a timezone offset")


@dataclass(frozen=True)
class Observation:
    observation_id: str
    installation_id: str
    session_id: str
    source: str
    source_event_id: str
    captured_at: str
    raw_bytes: bytes
    source_participant_id: str | None = None
    source_version: str = "unknown"
    metrics: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    def validate(self) -> None:
        for key in ("observation_id", "installation_id", "session_id", "source", "source_event_id"):
            if not getattr(self, key):
                raise ValueError(f"Missing {key}")
        validate_timestamp(self.captured_at)
        if not isinstance(self.raw_bytes, bytes):
            raise TypeError("raw_bytes must contain source bytes")
        if not self.raw_bytes:
            raise ValueError("Source payload must not be empty")
        if self.source_participant_id is not None and not self.source_participant_id.strip():
            raise ValueError("Participant ID must be nonempty when present")
        for name, metric in self.metrics.items():
            if not isinstance(metric, Mapping):
                raise ValueError(f"Metric {name!r} must be a mapping")
            kind = metric.get("kind")
            if kind not in SUPPORTED_KINDS:
                raise ValueError(f"Metric {name!r} has unsupported kind {kind!r}")
            if "value" not in metric:
                raise ValueError(f"Metric {name!r} must explicitly specify its value")
            if metric["value"] is None and kind != "unknown":
                raise ValueError(f"Metric {name!r}: null value must have kind 'unknown'")
            if not metric.get("unit"):
                raise ValueError(f"Metric {name!r} must specify unit; use 'unitless' where appropriate")
