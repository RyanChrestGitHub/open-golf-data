# Automated engineering work loop

## Initial condition S0

- Testable project mission and immutable-data contracts (`AGENTS.md`, RFC-0001).
- Deterministic synthetic fixture and executable replay laboratory.
- CI on pushes and PRs; no paid agent or secrets required to run tests.
- A staged issue backlog and hardware evidence request template.
- Explicit risk classification: inaccessible source data and absent identity signals are hard information boundaries.

## Recurring cycle

1. **Observe:** Contributor files hardware evidence, CI fails, or an external research scout identifies a vendor change.
2. **Classify:** Create a uniquely referenced evidence item. Distinguish an announcement or anecdote from an authorized physical recording.
3. **Specify:** Create one narrowly bounded issue with reproducer, expected result and success/failure conditions.
4. **Implement:** An agent proposes a small PR and adds tests without changing the frozen invariants.
5. **Verify:** Deterministic CI, independent review and (for hardware claims) signed physical test protocol.
6. **Integrate:** Maintainer approves changes and updates the compatibility evidence.
7. **Repeat:** New evidence and CI observations become inputs. A failed validation does not rewrite the verified baseline.

## GitHub configuration

Set branch protection / required CI, restrict write access, and do not permit direct pushes to `main` once published. Enable agent-driven issue triage and PRs only after reviewing workflow permissions and adding an appropriate AI engine secret. A **manual-only, read-only** `openai/codex-action` review workflow is bundled, but will not run until the maintainer supplies an OpenAI API key secret and triggers it. Agentic workflows that write PRs are **not** yet configured.

On a public repository: public issues and PR content are adversarial input. Do not automatically feed raw issue text into a privileged coding agent with repository write tokens and cloud credentials. Use manual or maintainer-gated requests at first. Never execute submitted fixture content as code. Keep hardware diagnostics opt-in and private unless sanitized.

## Recommended first agent tasks

A. Design a versioned real fixture manifest and private-evidence intake process without implementing upload yet.
B. Add a second deterministic fixture that detects missing fields and simulates a source file written in multiple fragments.
C. Add an explicit `EventAssociation` type and matching tests that allow abstention rather than guessing.
D. Prototype a read-only, authorized native-file adapter against an **approved sanitized sample** once obtained.

## Operating budget

Initially, one coding agent is sufficient. Cap repair attempts per issue, limit CI resource usage, require independent review, and keep compatibility claims evidence-backed. A full-time swarm of agents is not a prerequisite.
