"""Local, source-agnostic evidence staging; does not upload, parse, or run input."""

import hashlib
import json
import shutil
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def _candidate_format(prefix: bytes) -> str:
    """Return an *unverified* syntax hint, never a certified source format."""
    if not prefix:
        return "empty"
    text = prefix[:4096].decode("utf-8-sig", errors="replace").lstrip()
    if text.startswith("{") or text.startswith("["):
        return "json-candidate"
    if "\0" in text:
        return "binary-or-opaque"
    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].count(",") >= 1:
        return "csv-candidate"
    return "unknown-or-text"


def stage_evidence(
    path: Path,
    output: Path,
    *,
    device: str = "unknown",
    software: str = "unknown",
    version: str = "unknown",
    route: str = "unknown",
    kind: str = "unknown",
) -> dict:
    """Store unchanged bytes locally with a safe receipt. Never auto-publish or execute."""
    path = Path(path)
    output = Path(output)
    if not path.is_file():
        raise ValueError("Input must be a regular file")
    if path.is_symlink():
        raise ValueError("Symlink input is not allowed")
    h = hashlib.sha256()
    prefix = b""
    byte_count = 0
    with path.open("rb") as src:
        while block := src.read(CHUNK_SIZE):
            if not prefix:
                prefix = block[:4096]
            byte_count += len(block)
            h.update(block)
    digest = h.hexdigest()
    evidence_id = "ev-" + digest[:24]
    receipt = {
        "schema_version": 1,
        "evidence_id": evidence_id,
        "content_sha256": digest,
        "size_bytes": byte_count,
        "syntax_hint_unverified": _candidate_format(prefix),
        "source_claim": {
            "device": device,
            "software": software,
            "version": version,
            "route": route,
            "kind": kind,
        },
        "status": "local_unsubmitted",
        "real_hardware_verified": False,
        "publication_approved": False,
        "instructions": "Review original files for personal, facility, and proprietary data before any sharing. No public upload is performed.",
    }
    folder = output / evidence_id
    existing = folder / "receipt.json"
    if existing.exists():
        old = json.loads(existing.read_text(encoding="utf-8"))
        if old != receipt:
            raise ValueError("Previously staged content has different metadata; do not silently overwrite evidence")
    folder.mkdir(parents=True, exist_ok=True)
    original = folder / "source.bin"
    if not original.exists():
        shutil.copyfile(path, original)
    # Detect a source file changed while the copy was in progress.
    check = hashlib.sha256()
    with original.open("rb") as evidence:
        while block := evidence.read(CHUNK_SIZE):
            check.update(block)
    if check.hexdigest() != digest:
        raise ValueError("Staged bytes differ from source digest; investigate rather than overwriting evidence")
    if not existing.exists():
        existing.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
