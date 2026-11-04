"""Local, source-agnostic evidence staging; does not upload, parse, or run input."""

import hashlib
import json
import re
import shutil
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def verify_evidence(folder: Path) -> dict:
    """Read a v1 local receipt and rehash its bytes; do not certify provenance.

    Unknown receipt fields are retained. Matching bytes prove consistency with
    this receipt, not authenticity: someone can replace both bytes and receipt.
    This is not a filesystem sandbox or a concurrent-acquisition guarantee.
    """
    folder = Path(folder)

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate receipt field")
            result[key] = value
        return result

    try:
        receipt_path = folder / "receipt.json"
        payload_path = folder / "source.bin"
        for path in (folder, receipt_path, payload_path):
            if path.is_symlink():
                raise ValueError("Symlink evidence paths are not supported")
        if not receipt_path.is_file() or not payload_path.is_file():
            raise ValueError("Evidence requires regular receipt.json and source.bin files")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
        if not isinstance(receipt, dict):
            raise ValueError("Receipt must be a JSON object")
        version = receipt.get("schema_version")
        if type(version) is not int or version != 1:
            raise ValueError("Unsupported receipt schema version")
        digest = receipt.get("content_sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Receipt requires a lowercase SHA-256 digest")
        if receipt.get("evidence_id") != "ev-" + digest[:24]:
            raise ValueError("Receipt evidence ID does not match its digest")
        size = receipt.get("size_bytes")
        if type(size) is not int or size < 0:
            raise ValueError("Receipt size_bytes must be a nonnegative integer")
        claim = receipt.get("source_claim")
        if not isinstance(claim, dict) or any(
            not isinstance(claim.get(key), str)
            for key in ("device", "software", "version", "route", "kind")
        ):
            raise ValueError("Receipt requires string source claims")
        if any(not isinstance(receipt.get(key), str)
               for key in ("syntax_hint_unverified", "instructions")):
            raise ValueError("Receipt requires syntax hint and instructions strings")
        if (receipt.get("status") != "local_unsubmitted"
                or receipt.get("real_hardware_verified") is not False
                or receipt.get("publication_approved") is not False):
            raise ValueError("Expected an unsubmitted, unverified local staging receipt")
        check = hashlib.sha256()
        count = 0
        with payload_path.open("rb") as payload:
            while block := payload.read(CHUNK_SIZE):
                count += len(block)
                check.update(block)
        if check.hexdigest() != digest or count != size:
            raise ValueError("Staged payload digest or size differs from receipt")
    except (OSError, UnicodeError) as exc:
        raise ValueError("Cannot read staged evidence") from exc
    return receipt


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
