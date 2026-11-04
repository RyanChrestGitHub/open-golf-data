"""Bounded local syntax probes. No adapter, metric or provenance inference."""

import csv
import hashlib
import io
import json
from itertools import islice
from pathlib import Path

from .intake import verify_evidence

MAX_BYTES = 64 * 1024
MAX_DEPTH = 32
MAX_RECORDS = 256


def _exceeds_depth(text: str) -> bool:
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                return True
        elif char in "]}":
            depth -= 1
    return False


def _reject_constant(value):
    raise ValueError("Nonstandard JSON constant")


def _probe(data: bytes) -> tuple[str, str, str, str]:
    """Return syntax, inspection status, static reason, and decoding method."""
    if not data:
        return "empty", "complete", "empty_payload", "not_applicable"
    if b"\x00" in data:
        return "opaque-or-binary", "abstained", "nul_bytes", "unknown"
    encoding = "utf-8-sig" if data.startswith(b"\xef\xbb\xbf") else "utf-8"
    try:
        text = data.decode(encoding)
    except UnicodeDecodeError:
        return "unknown", "abstained", "unsupported_encoding", "unknown"
    stripped = text.lstrip()
    # Check nesting outside strings before handing text to the JSON parser.
    if _exceeds_depth(text):
        return "unknown", "abstained", "depth_limit", encoding
    try:
        json.loads(text, parse_constant=_reject_constant)
    except (ValueError, RecursionError):
        if stripped.startswith(("{", "[")):
            return "unknown", "abstained", "malformed_json_candidate", encoding
    else:
        return "json", "complete", "json_parsed", encoding
    try:
        rows = list(islice(csv.reader(io.StringIO(text, newline=""), strict=True), MAX_RECORDS + 1))
    except csv.Error:
        return "unknown", "abstained", "invalid_or_limited_csv", encoding
    if len(rows) > MAX_RECORDS:
        return "unknown", "abstained", "record_limit", encoding
    if len(rows) >= 2 and len(rows[0]) >= 2 and all(len(row) == len(rows[0]) for row in rows):
        return "csv-candidate", "complete", "consistent_csv_rows", encoding
    return "unknown", "abstained", "insufficient_or_ambiguous_syntax", encoding


def inspect_evidence(folder: Path) -> dict:
    """Verify all bytes, then probe at most MAX_BYTES; leave evidence unchanged.

    The integrity pass is streaming over the entire file. Only the syntax probe
    is byte-limited. A matching receipt is not authenticated provenance. This
    function does not isolate a concurrently modified filesystem or run input.
    """
    folder = Path(folder)
    receipt = verify_evidence(folder)
    report = {
        "inspection_schema_version": 1,
        "evidence_id": receipt["evidence_id"],
        "content_sha256": receipt["content_sha256"],
        "method": "bounded_json_then_comma_csv_v1",
        "limits": {"syntax_bytes": MAX_BYTES, "json_depth": MAX_DEPTH, "csv_records": MAX_RECORDS},
        "integrity_matches_receipt": True,
        "syntax": "unknown",
        "inspection_status": "abstained",
        "reason": "byte_limit",
        "encoding": "unknown",
        "adapter": None,
        "adapter_selection": "abstained",
        "provenance_verified": False,
        "hardware_verified": False,
        "next_action": "manual_source_and_permission_review",
        "uncertainty": "Syntax does not establish source, metric semantics, permissions or compatibility.",
    }
    if receipt["size_bytes"] > MAX_BYTES:
        return report
    try:
        with (folder / "source.bin").open("rb") as source:
            data = source.read(MAX_BYTES + 1)
    except OSError as exc:
        raise ValueError("Cannot read staged payload for inspection") from exc
    if len(data) != receipt["size_bytes"] or hashlib.sha256(data).hexdigest() != receipt["content_sha256"]:
        raise ValueError("Staged payload changed after integrity verification")
    syntax, status, reason, encoding = _probe(data)
    report.update(syntax=syntax, inspection_status=status, reason=reason, encoding=encoding)
    return report
