# Engineering playbook

Practical knowledge for the next engineering session. This is a maintained index
of evidence, not a second instruction authority. The currently merged
[AGENTS.md](../AGENTS.md) governs work; this playbook cannot grant permissions,
relax invariants, or authorize its own amendments. Proposed RFCs describe intent,
not verified capabilities. If a note conflicts with the contract or current code,
follow the contract, investigate, and correct or remove the note in a reviewed PR.

## Local development and verification

Run from the repository root with Python 3.10+ ([package metadata](../pyproject.toml)).
The laboratory and tests use the standard library: no install, API key, network
service, or hardware is needed for these commands.

```bash
python -m unittest discover -s tests -v
python -m open_golf_data demo --output lab-output
python -m open_golf_data demo --output lab-output
python -m open_golf_data inspect lab-output/events.sqlite
```

On a fresh output directory the first demo inserts five observations; the second
inserts zero. Both leave five observations, four attributed and one unclaimed.
An existing fixture ledger may already insert zero on the first run. Reuse the
directory to check restart recovery; use a separate output directory when a fresh
run is needed, preserving existing data. The demo writes `report.json`, the SQLite
ledger, and JSON/CSV exports for fictional `golfer-001` and `golfer-002`.
Replays rewrite reports and exports; the second report records zero insertions.
The output directory is [gitignored](../.gitignore), not a privacy control.

The [CLI test](../tests/test_cli.py), [ledger tests](../tests/test_ledger.py), and
[intake tests](../tests/test_intake.py) exercise synthetic replay, immutable source
bytes, conflicts, attribution boundaries, and local evidence staging.
Every reopened test ledger needs its own cleanup callback: closing the original
connection does not close its replacement, and Windows cannot remove an open
SQLite database. The native symlink intake test explicitly skips Windows error
1314 when link creation lacks privileges; a separate mocked-path test always
checks rejection before staging. The mock does not establish OS symlink behavior.
The [intake integrity tests](../tests/test_intake_integrity.py) check empty and
multi-chunk byte preservation, corruption of an existing staged copy, and source
changes between hashing and copying. A digest mismatch raises an error without
overwriting the staged bytes or issuing a new receipt. A failed initial copy can
leave a directory containing mismatched bytes without a receipt; retain it for
investigation rather than treating directory existence as successful staging.
These deterministic checks do not establish crash-safe or concurrent acquisition.

Run `python -m open_golf_data verify-evidence path/to/evidence-directory` to
validate an existing v1 local receipt and rehash its `source.bin` without the
original source file. Success reports `integrity_matches_receipt: true` and
`provenance_verified: false`; invalid, missing or mismatched inputs exit nonzero.
The command is read-only and preserves unknown receipt fields. It accepts only
local, unsubmitted receipts with no publication or hardware approval; it does
not upgrade claims, repair files, authenticate provenance or authorize sharing.
Replacing both receipt and payload can produce a matching pair. See the
[verification tests](../tests/test_evidence_verification.py); path checks are
not a filesystem sandbox or protection against concurrent path changes.

[CI](../.github/workflows/ci.yml) runs the suite and demo/inspection on Python 3.10
and 3.13. Local success on one interpreter does not establish those CI results.
The [documentation check](../tests/test_documentation.py) checks local inline file
links in the handoff documents; it does not validate external links, anchors,
prose accuracy, or arbitrary commands. Run the commands above to verify behavior.

## Where behavior lives

| Area | Implementation and evidence | Operational consequence |
| --- | --- | --- |
| Fixture replay | [fixture.py](../open_golf_data/fixture.py), [synthetic fixture](../open_golf_data/fixtures/synthetic_session.json) | Schema version 1; fictional native payloads are serialized for the demo. Real adapters must preserve acquired bytes rather than reconstruct them. |
| Ledger and exports | [ledger.py](../open_golf_data/ledger.py), [ledger tests](../tests/test_ledger.py) | SQLite persists observations and explicit session participant links; identical replays are idempotent, conflicting source events and identity reassignment raise errors. JSON/CSV retain raw bytes as base64; exports check their SHA-256 digest. |
| Local intake | [intake.py](../open_golf_data/intake.py), [intake tests](../tests/test_intake.py) | Evidence is staged under a content-derived ID with `source.bin` and `receipt.json`; metadata conflicts fail instead of silently overwriting a receipt. Syntax hints are unverified. Nothing is uploaded. |
| CLI | [cli.py](../open_golf_data/cli.py) | `demo`, `inspect`, and `evidence` operate locally. A local golfer ID filters exports; it is not authentication. |

For an authorized source file, `python -m open_golf_data evidence path/to/file
--output lab-evidence` stages unchanged bytes locally. Replace `path/to/file` with
the actual authorized file; do not run submitted content. Intake is not a privacy
filter or publication approval. Keep real evidence private until explicitly
authorized and reviewed; an ignored directory alone does not make sharing safe.

## Design context and limits

- [RFC-0001](RFC-0001.md) explains observations, measurement kinds, attribution,
  and export design. Event association, real authentication, and consent remain
  unresolved; do not infer identity or combine device/simulator observations.
- [RFC-0002](RFC-0002-EVIDENCE-INTAKE.md) explains source-agnostic intake and
  evidence promotion. An unknown format is valid intake, not a verified adapter.
- [LAB-0001](LAB-0001.md) defines synthetic versus physical evidence and the
  first hardware protocol. Passing fixtures does not establish physical accuracy,
  complete device coverage, live integration, or authenticated player handoff.
- [AGENT-LOOP](AGENT-LOOP.md) describes draft PRs, deterministic CI, independent
  review, and human merge. Use the current contract for the approval gates.
  The optional API-based review workflow is not required for local tests; do not
  enable paid services or add credentials just to run this workflow.

## Keeping knowledge useful

When implementation, architecture, or a repeatable operational finding changes,
update the affected note in the same PR, or explain why no update is needed.
Prefer a short finding with a source/test link, a reproducible check, and its
limits over a session transcript. Revalidate affected commands and references;
replace or remove stale claims rather than accumulating contradictory advice.
Do not store secrets, personal records, private logs, or machine-specific access
failures here as universal repository facts.

For each new session, inspect the current code and contract and rerun the relevant
checks before relying on a note. Separate observed behavior from hypotheses and
pending evidence. A passing link check cannot certify a claim. Changes to
`AGENTS.md` must be explicitly identified in the PR with rationale for maintainer
review; proposed text does not authorize the current session. Keep the existing
hard constraints and human merge gate intact.
