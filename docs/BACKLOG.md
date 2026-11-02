# Initial GitHub issue backlog

Open these as actual issues after the repository is published. The first four are ordered; everything else is conditional.

| ID | Priority | Title | Exit criterion |
| --- | --- | --- | --- |
| S0-001 | P0 | Bootstrap versioned evidence manifest and fixture validation | Schema rejects ambiguous metadata; all synthetic tests pass |
| S0-002 | P0 | Propose stable event association without inventing shot matches | Two distinct records link only when independent evidence exists |
| E001 | P0 | Find an authorized native Uneekor/GSPro measurement route | Original sample, software versions, field inventory, access agreement |
| E003 | P0 | Implement first native fixture replay adapter | Source byte fidelity and field coverage report against native fixture |
| E002 | P1 | Verify shared-bay participant attribution | Controlled alternating-player ground truth; unclaimed state when unknown |
| CLOUD-001 | P1 | Design and threat-model authenticated golfer handoff | OAuth/OIDC choice, consent model, per-account access controls and tests |
| AGENT-001 | P1 | Enable manually approved, least-privilege coding agent PR cycle | One scoped issue yields PR, tests, review, no auto merge |
| COMP-001 | P2 | Publish version-specific compatibility registry | Evidence links, verification statuses and expiration/staleness rules |
| SRC-002 | P2 | Add second hardware family using an existing bridge | Controlled native fixture with permission; equal local schema contract |

## Definition of done for an engineering issue

The PR includes tests for success and rejection, preserves native payload bytes, documents scope of the source evidence, does not claim real authentication from a fixture, and lists both verified facts and unknowns.
