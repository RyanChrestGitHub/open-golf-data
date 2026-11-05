"""Read the v1 archival table profile, independently of source adapters."""

import json
import re
from pathlib import Path


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate archive object key")
        result[key] = value
    return result


def read_archive(path: Path, *, expected_source_sha256: str) -> dict:
    """Load a selected table projection linked to an independently known digest.

    Column names are source labels. Null units mean unknown. Cells preserve
    lexical text, including empty strings, and null means a missing cell.
    Row order describes the projection, with no event or timestamp semantics.
    """
    table = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(table, dict) or table.get("profile") != "ogd-archive-table-v1":
        raise ValueError("unsupported archive profile")
    source = table.get("source")
    if not isinstance(source, dict):
        raise ValueError("archive source required")
    for key in ("label", "revision", "provenance", "selection"):
        if not isinstance(source.get(key), str) or not source[key].strip():
            raise ValueError(f"archive source {key} required")
    digest = source.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch("[a-f0-9]{64}", digest):
        raise ValueError("invalid archive source digest")
    if digest != expected_source_sha256:
        raise ValueError("archive source digest mismatch")

    columns = table.get("columns")
    if not isinstance(columns, list) or not columns:
        raise ValueError("archive columns required")
    names = set()
    for column in columns:
        if not isinstance(column, dict):
            raise ValueError("invalid archive column")
        name = column.get("name")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("invalid or duplicate archive column name")
        names.add(name)
        unit = column.get("unit")
        if "unit" not in column or (unit is not None and
                                    (not isinstance(unit, str) or not unit.strip())):
            raise ValueError("archive column unit must be text or null")
    rows = table.get("rows")
    if not isinstance(rows, list):
        raise ValueError("archive rows required")
    for row in rows:
        if (not isinstance(row, list) or len(row) != len(columns) or
                any(cell is not None and not isinstance(cell, str) for cell in row)):
            raise ValueError("invalid archive row shape or cell type")
    return table
