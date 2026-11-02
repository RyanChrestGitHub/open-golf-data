# Initial GitHub issue backlog — evidence-driven, vendor-agnostic

Open the most relevant issues after the public repository exists. Source adapters enter the backlog only **after evidence arrives**, not because a device was preselected.

| ID | Priority | Title | Exit criterion |
| --- | --- | --- | --- |
| S0-001 | P0 | Bootstrap versioned evidence manifest and fixture validation | Arbitrary inputs retained unchanged; unknown source is valid; never auto-published |
| INTAKE-001 | P0 | Secure, contributor-friendly evidence handoff | Metadata-only issue form and approved private source transfer; no public PII |
| INTAKE-002 | P0 | Add deterministic format inspection and evidence-based routing | Known -> replay test; unknown -> research issue; regression -> adapter repair issue; duplicates linked |
| AGENT-001 | P0 | Enable manually approved, least-privilege coding agent PR cycle | One scoped issue yields draft PR, tests, independent review, request for maintainer approval; no auto-merge |
| S0-002 | P1 | Propose stable event associations without inventing shot matches | Separate records link only when evidence supports relationship |
| E001 | P1 | Validate accessibility of **first viable contributed physical source** | Authorized original sample, software versions, field inventory and reproducible access route |
| E003 | P1 | Replay first real evidence and assess coverage | Original bytes retained, field inventory and observed-vs-expected reconciliation |
| E002 | P1 | Verify shared-bay participant attribution when a source supports it | Controlled ground truth; remain unclaimed if identity signals are absent |
| CLOUD-001 | P2 | Threat-model authenticated golfer handoff | OIDC, consent, local retention, per-account access controls and tests |
| COMP-001 | P2 | Publish version-specific compatibility registry | Evidence links and verification statuses, including unsupported/unknown |
| SRC-002 | P2 | Add second independently verified hardware family | Reproducible evidence and retained source-specific fields |

## Definition of done for an engineering issue

A PR links evidence, states precisely what is verified, adds success and negative tests, preserves original source payloads, and does not imply real hardware success from synthetic or export-only data. Request maintainer approval when ready. A submission alone does not mandate a PR or publishable fixture.
