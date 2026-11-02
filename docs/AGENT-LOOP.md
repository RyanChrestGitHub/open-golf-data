# Automated engineering work loop

## Initial condition S0

- Testable project mission and immutable-data contracts (`AGENTS.md`, RFC-0001).
- Deterministic synthetic fixture and executable replay laboratory.
- CI on pushes and PRs; no paid agent or secrets required to run tests.
- A staged issue backlog and hardware evidence request template.
- Explicit risk classification: inaccessible source data and absent identity signals are hard information boundaries.

## Recurring cycle

1. **Observe:** Contributor offers any authorized device data, CI fails, or an external research scout identifies a vendor change.
2. **Classify:** Stage exact source bytes locally or privately and create a uniquely referenced evidence item. Vendor/source unknown is acceptable. Distinguish an announcement from a real recording.
3. **Route and specify:** Recognized source -> adapter regression issue if needed; unknown source -> research issue; unsupported access -> evidence request. Create one bounded task, avoid an issue or PR for every duplicate upload.
4. **Implement:** When evidence supports a code change, an agent opens a **draft** PR with tests without changing the frozen invariants.
5. **Verify:** Deterministic CI, independent review and (for hardware claims) signed physical test protocol.
6. **Ready for review:** Agent requests maintainer review only when CI passes, security/privacy gates are met and compatibility claims are correctly qualified. Maintainer chooses merge, reject, or more evidence.
7. **Repeat:** New evidence and CI observations become inputs. A failed validation does not rewrite the verified baseline.

## GitHub configuration

Set branch protection / required CI, restrict write access, and do not permit direct pushes to `main` once published. Enable agent-driven issue triage and PRs only after reviewing workflow permissions and adding an appropriate AI engine secret. A **manual-only, read-only** `openai/codex-action` review workflow is bundled, but will not run until the maintainer supplies an OpenAI API key secret and triggers it. Agentic workflows that write PRs are **not** yet configured.

On a public repository: public issues and PR content are adversarial input. Do not automatically feed raw issue text into a privileged coding agent with repository write tokens and cloud credentials. Use manual or maintainer-gated requests at first. Never execute submitted fixture content as code. Keep hardware diagnostics opt-in and private unless sanitized.

## Recommended first agent tasks

A. Design a versioned real fixture manifest and private-evidence intake process without implementing upload yet.
B. Add a second deterministic fixture that detects missing fields and simulates a source file written in multiple fragments.
C. Add an explicit `EventAssociation` type and matching tests that allow abstention rather than guessing.
D. Prototype a source-specific read-only adapter against the **first approved, reproducible, sanitized sample from any device**, once obtained.

## Operating budget

Initially, one coding agent is sufficient. Cap repair attempts per issue, limit CI resource usage, require independent review, and keep compatibility claims evidence-backed. A full-time swarm of agents is not a prerequisite.

Detailed intake contract: [RFC-0002](RFC-0002-EVIDENCE-INTAKE.md).
