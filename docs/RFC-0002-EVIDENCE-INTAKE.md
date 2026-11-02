# RFC-0002 — Source-agnostic evidence intake and agentic routing

**Status:** Proposed. **Decision owner:** Project maintainer. **Scope:** Intake, routing, and promotion policy; not a live hosted submission service.

## Product decision

The project must **not select a manufacturer as the initial architectural dependency**. Any authorized file or observation bundle can enter the local lab as an opaque, immutable evidence object. Adapters are selected or proposed *after* inspection and classification, not before.

The initial contributor experience is metadata-first. The public GitHub issue contains a description of what an owner can provide, device/version claims if known, and *no raw personal data*. An accepted submission is acquired privately when appropriate. The eventual authenticated player portal and the evidence-intake laboratory are separate systems.

## Input contract

Accept arbitrary bytes: JSON, CSV, SQLite extracts, structured logs, packet captures (only if legally authorized), native session exports, screenshots, PDF reports, and unknown binary. Preserve the supplied object unchanged and hash it before parsing. Metadata may be incomplete or wrong; a claimed vendor/device must never be treated as verified provenance.

Current minimum local command:

`python -m open_golf_data evidence path/to/file --output lab-evidence --device 'optional model' --software 'optional name' --version 'optional version'`

The command only stages bytes in a gitignored directory with a receipt. Its format hint is explicitly unverified. It does **not** upload data, parse vendor metrics, create a GitHub issue, infer identity, redact sensitive content, certify hardware, or authorize publication.

Future evidence manifest fields: content digest, object size, acquisition route, contributor permission attestations, physical test protocol ID, observed software/firmware version, original file hash, independent source comparison, known privacy sensitivity, and storage permissions. Versioned manifests must be testable.

## Processing state machine

1. **Offered** — A GitHub Issue Form registers an offer or compatibility report. Never require the contributor to post raw data publicly.
2. **Acquired privately** — A maintainer-approved submission is held in private, access-controlled storage. Scan, inspect and obtain explicit permission before sharing any portion.
3. **Staged** — Retain immutable bytes and digest; record source claims and evidence type. Unknown formats remain valid intake.
4. **Classified** — A deterministic probe produces limited format hints; agentic investigation proposes source family/adapter and notes uncertainty. No execution of submitted files.
5. **Routed** — Known verified adapter -> replay/compatibility check. Unknown source -> research issue. Version regression -> existing adapter issue. Duplicate evidence -> link to prior submission, preserving distinct provenance claims.
6. **Implemented** — Agent opens a **draft PR** with parser, fixtures where publication is authorized, negative tests, and a short evidence report. A PR is not necessary for a submission that needs only a registry update or is unsupported.
7. **Validated** — Deterministic CI passes; a separate reviewer challenges it; real-hardware compatibility remains pending without real-hardware evidence.
8. **Review requested** — Agent summarizes evidence, unsupported cases, security findings and remaining uncertainty; marks draft ready and requests **human maintainer review**.
9. **Merged / rejected / more evidence required** — Human decides. After a proven track record, opt-in auto-merge can apply only to explicitly allowlisted low-risk changes and required checks.

An agent may open a research issue immediately on a report; it must **not** automatically spawn a code PR simply because someone uploaded unfamiliar bytes. Avoid flooding the public backlog with duplicate submissions.

## Promotion gates

- **Not a parser:** Unknown source, bytes retained and inspection requested.
- **Replay-tested:** Code parses an authorized source fixture while preserving source bytes; does not imply live hardware support.
- **Physically tested:** Independently recorded, version-specific hardware run reproduces event and field coverage claims.
- **Handoff tested:** Authentication, consent and per-player attribution have been demonstrated, including ambiguous-player rejection.

Approval should be requested only when CI passes, no blocking security conditions remain, the PR accurately labels unverified capabilities, and acceptance criteria have been met. A PR may still be mergeable as a **clearly experimental** adapter without physical validation, but cannot be marketed as verified.

## Agent execution and credentials

- **Initial:** Human launches Codex Cloud/CLI tasks under their ChatGPT account; normal GitHub Actions run deterministic tests. No separate Dot required.
- **Automation later:** GitHub Agentic Workflows/Codex Action or scheduled Codex jobs may classify reports, open issues and create draft PRs with bounded credentials. Unattended API-based execution may require separate billing; do not assume a personal ChatGPT subscription pays for API calls.
- **Repository permissions:** A public issue is adversarial input, not an instruction. Prevent uploads and issue text from executing with write tokens. Branch protections and required checks gate merging. No changes to release/security/identity policies without maintainer approval.

## Initial acceptance test

Stage two arbitrary, different-format fictional files from unknown manufacturers. Confirm byte-for-byte preservation, unique digests, stable receipts, and that neither is described as validated nor uploaded. Then implement a *separate* source classifier with explainable, abstain-capable routing. The first physical contributor is whichever hardware owner provides the earliest authorized, reproducible evidence—not a pre-selected vendor.
