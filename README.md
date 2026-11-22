# Open Golf Data

**Any launch monitor, any simulator, your data.**

We are building an open data contract so golfers can keep and reuse their
lawfully accessible launch-monitor outputs, and manufacturers and simulator
makers can support a common interface. This is our direction; universal
compatibility has not been demonstrated.

**Available today:** a local laboratory with a fictional-session demo, portable
JSON/CSV exports, unchanged-file evidence staging, integrity verification and
bounded JSON/CSV syntax inspection. Real hardware compatibility, live simulator
connections and authenticated golfer delivery remain unverified.

## Who it is for

- **Golfers:** keep an inspectable history and take it to other compatible tools.
- **Launch-monitor makers:** expose supported outputs through a documented contract
  while retaining their proprietary measurement technology.
- **Simulator and app makers:** consume a common model instead of rebuilding each
  source integration. Simpler integration is a goal we still need to test.

## What the contract must preserve

Keep the original source bytes and their digest alongside any standardized
representation. Retain units, unknown fields and missing values; distinguish
reported, vendor-estimated, simulated, calculated and unknown quantities. A
simulator result and a monitor observation are separate events unless evidence
supports linking them. Unknown player identity stays unassigned.

A portable file does not establish a live connection. Live observations,
readiness and control need separately specified interfaces, permissions and
tests. Normalizing accessible outputs does not require reproducing a maker's
proprietary measurement algorithms or assuming access to every device.

The collector and portable history are open source. Analytics and AI coaching
are outside this project's scope. See [product direction](docs/PRODUCT-DIRECTION.md)
for the proof sequence and the limits on compatibility claims.

## Run Laboratory 0001

Requires Python 3.10+; the demo uses only Python's standard library.

```bash
python -m unittest discover -s tests -v
python -m open_golf_data demo --output lab-output
python -m open_golf_data inspect lab-output/events.sqlite
```

Or install the local CLI:

```bash
python -m pip install -e .
ogd demo --output lab-output
```

Outputs:

- `events.sqlite` — local, append-only event ledger (SQLite database).
- `golfer-001.json`, `golfer-001.csv` — observations mapped to a **fictional** golfer across home and commercial installations.
- `golfer-002.json`, `golfer-002.csv` — separate fictional golfer's data.
- `report.json` — inserted / attributed / unclaimed event counts.

The demo includes five independent observations: one native-like device observation and one simulator outcome for player A, one for player B, one **unattributed** record, and a second home-lab observation for player A. The simulated values are fictional and do not validate physical measurement accuracy. Run it twice to verify replay idempotency and restart recovery.

### What it tests

| Contract | Demonstrated | Not yet demonstrated |
| --- | --- | --- |
| Original source bytes preserved | Yes | Native binary device interface |
| Unknown fields retained | Yes | Completeness of any commercial monitor |
| Estimated, simulated and reported values kept distinct | Yes | Validation of manufacturer semantics |
| Repeated event does not duplicate | Yes | Windows file watcher crash conditions |
| Conflicting source event rejected | Yes | Live stream sequence recovery |
| Home/facility share observation model | Yes | Real authenticated cloud access |
| Unattributed records excluded from per-player export | Yes | Four-player real-world identity accuracy |
| Player history exports CSV and JSON | Yes | Secure remote portal and API |

## Inspect a common archival metric offline

From a fresh checkout, run this command with the included fictional archive and
mapping configuration. It prints one JSON metric view to standard output.

```bash
python -m open_golf_data metric-view examples/fictional_archive.json --mappings examples/fictional_mappings.json --source-sha256 abababababababababababababababababababababababababababababababab --key ball_speed
```

The result includes raw lexical values, missing/blank status, the source field
and unit, mapping provenance, confidence and metric kind. Use `--key
unknown_quantity` or `--key duration` with the same command to see unknown and
conflicting units. The duration example retains its numbers without rescaling.
All example values and the source digest are invented.

For an authorized archival table, supply its path, independently known source
digest and a JSON list of explicit mappings. Each mapping binds a common key to
an exact source field and digest. The consumer command stays the same across
source layouts. This is a read-only view. Its JSON can contain sensitive source
values, so keep real output within its approved storage and sharing scope.
See the [engineering playbook](docs/ENGINEERING-PLAYBOOK.md) for the mapping API
and interpretation limits.

## Project an explicitly selected fictional CSV

Run from a fresh checkout with Python 3.10+. Use a new output path; the
projection command refuses existing outputs. This example uses three fictional
records, including a quoted comma/newline, blanks, lexical zeros and repeats.

```bash
python -m open_golf_data demo --output lab-output
python -m open_golf_data evidence examples/fictional_projection.csv --output lab-evidence
python -m open_golf_data project-csv lab-evidence/ev-6a09228c0c58c1de7d98b984 --config examples/fictional_projection.json --output lab-output/projection.json
python -m open_golf_data metric-view lab-output/projection.json --mappings examples/fictional_projection_mappings.json --source-sha256 6a09228c0c58c1de7d98b984f3766b271d8ee21bc384f29b3f74ef14de744c87 --key ball_speed
```

The first command creates `lab-output` using the existing synthetic demo.
The pinned source SHA-256 above is computed
from the included fictional CSV bytes. Staging retains its bytes and receipt;
projection verifies them and writes a separate archival table. `ball_speed`
returns `"0.00"`, `""`, `"0.00"` with `conflicting` unit status (declared mph,
expected km/h), tentative confidence and unknown kind. No conversion occurs.
The Note column retains its quoted text and unknown unit, even though this
metric request selects only Speed.

[Selection configuration](examples/fictional_projection.json) explicitly supplies
UTF-8/comma syntax, one-based header/first/last **parsed record** ordinals,
exact unique column names, units (text or null), source label/revision,
provenance and selection rationale. Quoted newlines do not increment record
ordinals. Unselected fields remain in the original source; the archive records
its range/field selection. Missing selected cells are rejected as ragged records,
not invented as nulls; CSV empty fields remain blank strings.

Limits: at most 1 MiB input and 20 selected records, strict UTF-8 without BOM or
NUL, comma/double-quote CSV, at least two unique nonempty header fields. Other
encodings/dialects, malformed CSV, ambiguous headers, invalid ranges/fields,
changed staged bytes and existing outputs fail without publishing an archive.
No dialect sniffing, units/identity inference, XLSX, adapter or physical claim.
This command is not a privacy filter or publication permission; keep real inputs
and derived outputs within their authorized handling scope. Local receipt
integrity does not authenticate provenance or protect against concurrent path
changes. Output publication uses a same-directory temporary file and a
non-overwriting hard link; filesystems without hard-link support fail closed.
### Use the same key for a second fictional source

The first command below repeats the existing example. The second uses the same
consumer command and `ball_speed` key with a different source label, field and
unit. Both run from a fresh checkout with no source-specific consumer code.

```bash
python -m open_golf_data metric-view examples/fictional_archive.json --mappings examples/fictional_mappings.json --source-sha256 abababababababababababababababababababababababababababababababab --key ball_speed
python -m open_golf_data metric-view examples/fictional_second_archive.json --mappings examples/fictional_mappings.json --source-sha256 cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd --key ball_speed
```

| Result | First source | Second source |
| --- | --- | --- |
| Source field / unit | Example speed / mph | Velocity / km/h |
| Mapping confidence / kind | tentative / unknown | unknown / unknown |
| Unit status | declared | conflicting (expected mph, declared km/h) |
| Raw values | `"0.00"`, null, `""` | `"000.00"`, `"1.2300"`, `"1.2300"` |

The conflict is intentional: values remain unchanged, with no conversion,
arithmetic, row matching or comparison implied. Inspect units and uncertainty
before using values. For a missing-unit example, rerun the first command with
`--key unknown_quantity`; its unit status is `unknown`. These invented source
links demonstrate configurable archival interpretation, not physical validation
or a universal metric standard.

For an existing third-party fixture, the [two-metric consumer recipe](docs/SQUARESTATS-CONSUMER-RECIPE.md)
provides explicit selection and mappings with source, rights and physical-evidence limits.

## Bring evidence from any source

We welcome evidence from any manufacturer: native exports, logs, reports, screenshots, protocol examples and unknown formats. Each has a different use. A research table or hand-written protocol example can inform the contract without proving a native export or physical integration. The first hardware integration will follow authorized, reproducible evidence.

Stage your own file locally without sending it anywhere:

```bash
python -m open_golf_data evidence path/to/file --output lab-evidence --device "optional model" --software "optional software" --version "optional version"
```

The command computes a digest, preserves the original bytes as `source.bin`, and writes a local `receipt.json` with unverified format hints. The `lab-evidence/` directory is gitignored. **This is not an upload, adapter, privacy filter, source verification, or certification.** Review all files for personal/facility information before sharing.

Check a staged directory without changing it:

```bash
python -m open_golf_data verify-evidence path/to/evidence-directory
python -m open_golf_data inspect-evidence path/to/evidence-directory
```

Verification checks bytes against the saved receipt. Inspection checks supported
syntax within fixed limits and can decline to classify a file. Neither command
establishes source authenticity, metric meaning, permission to share, or hardware
support. See the [engineering playbook](docs/ENGINEERING-PLAYBOOK.md) for limits.

[Evidence intake and routing proposal](docs/RFC-0002-EVIDENCE-INTAKE.md)

## The next three milestone issues

1. **INTAKE-001, generic evidence handoff:** Register evidence offers via public metadata-only GitHub issues; stage arbitrary authorized source files privately without assuming a vendor. Design a secure reviewer-controlled transfer process before accepting public submissions.
2. **INTAKE-002, classification and routing:** Detect candidate formats, link duplicates, determine whether an adapter exists, and abstain or create an actionable research issue when evidence is insufficient.
3. **E001–E003, first physical evidence:** Select the first authorized, reproducible hardware source from submissions. Test source accessibility, identity attribution when possible, and field/event fidelity. Do not promise physical verification from replay alone.

**Do not purchase a simulator or deploy code to a commercial machine solely to complete the synthetic stage.** The first physical experiment requires the installation owner's permission and a suitable, controlled observation session; no hardware manufacturer is required first.

## Engineering system

Start with the [documentation guide](docs/README.md) for project design, evidence handling and contributor workflows.

- [Agent instructions](AGENTS.md)
- [Engineering playbook](docs/ENGINEERING-PLAYBOOK.md)
- [Architecture RFC](docs/RFC-0001.md)
- [Source-agnostic evidence intake RFC](docs/RFC-0002-EVIDENCE-INTAKE.md)
- [Evidence and physical test protocol](docs/LAB-0001.md)
- [Agentic work loop](docs/AGENT-LOOP.md)
- [Issue backlog](docs/BACKLOG.md)
- [Security and privacy](docs/SECURITY.md)

CI runs the deterministic tests on supported Python versions. **The optional Codex review workflow is manual-only** and requires you to set `OPENAI_API_KEY` as a repository secret before dispatch; it produces a review artifact, not code changes. No scheduled scout, autonomous coding PRs, private upload service, or remote sync is activated by this bootstrap. Those require explicit GitHub configuration and a validated threat model.

## Contributing

Start with nonpersonal source descriptions and the interface or export you can
lawfully access. Keep real player records private; agree a permitted transfer and
review process before sharing files. Technical acceptance and compatibility
claims require reproducible evidence. Follow the [agent instructions](AGENTS.md)
and [security guidance](docs/SECURITY.md).

The repository's MIT license does not settle the rights to every external dataset,
vendor interface or future driver. Record the applicable source terms and allowed
uses for each contribution.
