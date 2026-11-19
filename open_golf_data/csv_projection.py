"""Explicit, local CSV projections; no source or measurement inference."""

import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile

from .archive_table import _unique_object, read_archive
from .intake import verify_evidence

MAX_BYTES = 1024 * 1024
MAX_SELECTED_RECORDS = 20


def _validate_quotes(text: str) -> None:
    """Reject quotes in unquoted fields, which csv.reader otherwise accepts."""
    state = "start"
    for char in text:
        if state == "quoted":
            if char == '"':
                state = "closed"
        elif state == "closed":
            if char == '"':
                state = "quoted"
            elif char == ',':
                state = "start"
            elif char in '\r\n':
                state = "start"
            else:
                raise ValueError("text after closing CSV quote")
        elif char == '"':
            if state != "start":
                raise ValueError("quote in unquoted CSV field")
            state = "quoted"
        elif char == ',' or char in '\r\n':
            state = "start"
        else:
            state = "plain"
    if state == "quoted":
        raise ValueError("unterminated CSV quote")


def project_csv(evidence: Path, config: Path, output: Path) -> dict:
    """Write a new archive only after validating a bounded staged CSV snapshot.

    Ordinals are one-based parsed CSV records, never physical lines. Integrity
    against a local receipt is not provenance or publication authorization.
    """
    evidence, config, output = Path(evidence), Path(config), Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("output already exists")
    if output.resolve().is_relative_to(evidence.resolve()):
        raise ValueError("output must be outside staged evidence")
    spec = json.loads(config.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    required = {"encoding", "delimiter", "header_record", "first_record", "last_record",
                "columns", "label", "revision", "provenance", "selection"}
    if not isinstance(spec, dict) or set(spec) != required:
        raise ValueError("explicit projection configuration required")
    if spec["encoding"] != "utf-8" or spec["delimiter"] != ",":
        raise ValueError("only UTF-8 comma CSV supported")
    for key in ("label", "revision", "provenance", "selection"):
        if not isinstance(spec[key], str) or not spec[key].strip():
            raise ValueError("source description required")
    for key in ("header_record", "first_record", "last_record"):
        if type(spec[key]) is not int:
            raise ValueError("integer record ordinals required")
    header, first, last = (spec[k] for k in ("header_record", "first_record", "last_record"))
    if not (1 <= header < first <= last) or last - first + 1 > MAX_SELECTED_RECORDS:
        raise ValueError("invalid or excessive record range")
    columns = spec["columns"]
    if not isinstance(columns, list) or not columns:
        raise ValueError("columns required")
    names = []
    for column in columns:
        if not isinstance(column, dict) or set(column) != {"name", "unit"}:
            raise ValueError("explicit name and unit required")
        name, unit = column["name"], column["unit"]
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("unique column names required")
        if unit is not None and (not isinstance(unit, str) or not unit.strip()):
            raise ValueError("unit must be text or null")
        names.append(name)
    receipt = verify_evidence(evidence)
    if receipt["size_bytes"] > MAX_BYTES:
        raise ValueError("CSV exceeds projection byte limit")
    # Rehash the exact snapshot parsed, rather than trusting an earlier read.
    with (evidence / "source.bin").open("rb") as source:
        payload = source.read(MAX_BYTES + 1)
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) != receipt["size_bytes"] or digest != receipt["content_sha256"]:
        raise ValueError("staged bytes changed")
    text = payload.decode("utf-8")
    if text.startswith('\ufeff') or '\0' in text:
        raise ValueError("BOM and NUL are unsupported")
    _validate_quotes(text)
    previous_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(MAX_BYTES)
        records = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    finally:
        csv.field_size_limit(previous_limit)
    if last > len(records):
        raise ValueError("selected records absent")
    fields = records[header - 1]
    if len(fields) < 2 or any(not name.strip() for name in fields) or len(set(fields)) != len(fields):
        raise ValueError("at least two unique nonempty header fields required")
    if any(name not in fields for name in names):
        raise ValueError("selected field absent")
    selected = records[first - 1:last]
    if any(len(row) != len(fields) for row in selected):
        raise ValueError("ragged selected CSV record")
    indices = [fields.index(name) for name in names]
    table = {"profile": "ogd-archive-table-v1",
             "source": {k: spec[k] for k in ("label", "revision", "provenance", "selection")},
             "columns": columns, "rows": [[row[i] for i in indices] for row in selected],
             "projection": {"format": "utf-8-comma-csv", "header_record": header,
                            "first_record": first, "last_record": last,
                            "total_records": len(records), "selected_fields": names}}
    table["source"]["sha256"] = digest
    # Verify again before publishing; no filesystem concurrency guarantee implied.
    if verify_evidence(evidence) != receipt:
        raise ValueError("staging receipt changed")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(table, indent=2) + "\n")
        read_archive(temporary, expected_source_sha256=digest)
        # Hard-link creation is atomic and fails if the destination exists.
        os.link(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink()
    return {"source_sha256": digest, "selected_records": len(selected)}
