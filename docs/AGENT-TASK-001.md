# First delegated coding task — S0-002

**Title:** Introduce evidence-backed event associations without conflating source observations.

## Intent

Real launch monitors and simulator software may produce separate events for the same physical attempt. Source timestamps are not proof of identity. Introduce a separate, versioned `EventAssociation` type, keeping observation records immutable.

## Requirements

1. Define a reversible, auditable relation of source observation IDs to a common attempt candidate.
2. Include evidence category, evidence reference, author/origin and a support status.
3. Reject references to absent observation IDs, cross-session assertions without explicit justification, and self-conflicting links.
4. Support `unassociated` events. Do not automatically pair the two synthetic events whose timestamps are close.
5. Preserve all prior tests and add tests for claimed matches, rejected ambiguity, and auditability after correction.
6. Update architecture RFC to explain what the association means and does **not** establish.

## Out of scope

No machine learning, heuristic player attribution, club fitting, cloud backend, vendor driver, implicit merging, or UI.

## Evidence needed

Synthetic tests establish that the association machinery behaves correctly. Real monitor-to-simulator matching remains unverified until Laboratory E001/E003 provides authorized physical evidence.

## Done

A small PR with tests, documentation, no unreviewed new dependencies, and the exact commands/results used to validate it.
