# Open Golf Data — Laboratory Bootstrap

> **Status: synthetic proof of architecture only.** Not a launch-monitor integration, authenticated portal, commercial deployment, or security-certified product.

## The purpose

Golfers should be able to retrieve and use the original measurements **exposed through supported, authorized launch-monitor interfaces**—whether they play at home or in a commercial simulator bay.

The collector and portable history are meant to be open source. Analytics and AI coaching are intentionally not part of this project.

A good handoff means source records are preserved, simulated and device-derived quantities are not conflated, the correct golfer receives the records, and the history can be exported without proprietary software. Unavailable data and ambiguous player identity must never be invented.

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

## The next three milestone issues

1. **E001, source accessibility:** Obtain permission to collect a small native Uneekor/GSPro sample. Document exposed fields, versions, file provenance and physical attempt count. Implement **read-only** fixture ingestion without changing normal play.
2. **E002, attribution:** Independently observe an alternating-player session; determine whether source-level participant IDs identify observations and if they can be linked to consenting real accounts. Unknown IDs stay unclaimed.
3. **E003, fidelity:** Reconcile physical attempts, device detections, native records and collector records. Prove byte-preserving export and explain missing fields and mismatches.

**Do not purchase a simulator or deploy code to a commercial machine solely to complete the synthetic stage.** The first physical experiment requires the installation owner's permission and a suitable, controlled observation session.

## Engineering system

- [Agent instructions](AGENTS.md)
- [Architecture RFC](docs/RFC-0001.md)
- [Evidence and physical test protocol](docs/LAB-0001.md)
- [Agentic work loop](docs/AGENT-LOOP.md)
- [Issue backlog](docs/BACKLOG.md)
- [First delegated coding task](docs/AGENT-TASK-001.md)
- [Security and privacy](docs/SECURITY.md)

CI runs the deterministic tests on supported Python versions. **The optional Codex review workflow is manual-only** and requires you to set `OPENAI_API_KEY` as a repository secret before dispatch; it produces a review artifact, not code changes. No scheduled scout, autonomous coding PRs, public submission ingestion, or remote sync is activated by this bootstrap. Those require explicit GitHub configuration and a validated threat model.

## Publishing to GitHub

Use a **new** repository, separate from any personal golf analysis files. The draft name `open-golf-data` can change. With the GitHub CLI authenticated:

```bash
git init
git add .
git commit -m "Bootstrap evidence-led open golf data laboratory"
gh repo create open-golf-data --public --source=. --push
```

Alternatively, create an empty public repository via GitHub's web UI (without a generated README), then add `origin` and push. Before publishing, review the license, your chosen repository name, and all bundled files.

The MIT license is a **starting suggestion**, not a determination that all future vendor drivers can be redistributed under MIT. Review dependencies and any vendor interface permissions before adding integrations.

## First public message

> We're building open, portable launch-monitor measurement history. The first release is a tested, synthetic local data ledger—not a claimed universal connector. We are looking for hardware owners willing to validate authorized interfaces and help document exactly which measurements are accessible on each device and software version. No private shot logs should be posted to public issues.
