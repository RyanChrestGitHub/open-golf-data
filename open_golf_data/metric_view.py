"""Read-only, explicitly mapped interpretations of archival table columns."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence
import re

from .archive_table import read_archive
from .models import SUPPORTED_KINDS


@dataclass(frozen=True)
class MetricMapping:
    """A source-digest-bound interpretation, supplied by the caller.

    Confidence describes the mapping evidence, never physical validation.
    expected_unit is an optional comparison, not a conversion instruction.
    """

    key: str
    source_sha256: str
    field: str
    provenance: str
    confidence: str
    kind: str = "unknown"
    expected_unit: str | None = None

    def validate(self) -> None:
        if not isinstance(self.key, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", self.key):
            raise ValueError("invalid metric key")
        if not isinstance(self.source_sha256, str) or not re.fullmatch(
                r"[a-f0-9]{64}", self.source_sha256):
            raise ValueError("invalid mapping source digest")
        for value in (self.field, self.provenance):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("mapping field and provenance required")
        if self.confidence not in ("unknown", "tentative", "supported"):
            raise ValueError("invalid mapping confidence")
        if self.kind not in SUPPORTED_KINDS:
            raise ValueError("invalid metric kind")
        if self.expected_unit is not None and (
                not isinstance(self.expected_unit, str) or not self.expected_unit.strip()):
            raise ValueError("invalid expected unit")


def read_metric(path: Path, *, expected_source_sha256: str, metric_key: str,
                mappings: Sequence[MetricMapping]) -> dict:
    """Return one mapped column in projection order, retaining raw lexical cells.

    Missing and ambiguous mappings fail. Units are compared literally, without
    normalization or inference. Returned rows are archival positions, not events.
    The source archive and mapping inputs are read-only.
    """
    table = read_archive(path, expected_source_sha256=expected_source_sha256)
    candidates = []
    for mapping in mappings:
        mapping.validate()
        if mapping.key == metric_key and mapping.source_sha256 == expected_source_sha256:
            candidates.append(mapping)
    if len(candidates) != 1:
        raise ValueError("exactly one source-bound metric mapping required")
    mapping = candidates[0]
    indices = [i for i, column in enumerate(table["columns"]) if column["name"] == mapping.field]
    if not indices:
        raise ValueError("mapped field absent from archive")
    index = indices[0]
    column = table["columns"][index]
    unit_status = "declared"
    if column["unit"] is None:
        unit_status = "unknown"
    elif mapping.expected_unit is not None and mapping.expected_unit != column["unit"]:
        unit_status = "conflicting"
    rows = []
    for row in table["rows"]:
        value = row[index]
        status = "present"
        if value is None:
            status = "missing"
        elif value == "":
            status = "blank"
        rows.append({"raw_value": value, "value_status": status})
    return {"metric_key": metric_key, "source": table["source"],
            "mapping": asdict(mapping), "source_column": column,
            "unit_status": unit_status, "rows": rows}
