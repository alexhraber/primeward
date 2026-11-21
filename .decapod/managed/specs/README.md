# Project Specs

## Project Purpose
Exact prime succession through reusable arithmetic state, with reproducible numerical physics applications.

## Authoring Scope and Evidence
Project: Primeward. This is an initial authoring scaffold, not an implementation attestation.

Describe the configured project from purpose to architecture to implementation depth. Start with the whole product: its users, problem, outcomes, and boundaries; then explain the system and its components, interfaces, state, operations, security, and proof. Ground factual prose in the repository's config, README/product documentation, source paths and symbols, contracts, and tests. Distinguish implemented behavior, intended behavior, assumptions, and unresolved gaps. A narrow task changes the relevant part of this whole-project account; it must not replace project-wide identity with the latest task, release workflow, or tooling. Record task-specific scope and evidence in the current change's governance record. Templates and declared capabilities are authoring/proof obligations, not evidence that a runtime guarantee exists. Preserve authored prose during generated refreshes. If configured metadata and explicit project-level sections are absent, leave project identity unknown and ask for or author grounded context rather than promoting an arbitrary legacy/task line.

Use the seeded context below as a starting point to verify against repository sources. Replace example diagrams, suggested controls, targets, tables, and blank fields with source-grounded prose; mark non-applicable topics with a reason. Do not adopt a store, queue, server, CI provider, replay guarantee, or service level merely because it appears in a template.

Canonical path: `.decapod/managed/specs/`.
These files are the project-local contract for humans and agents.

## Snapshot
- Project: Primeward
- Outcome: Exact prime succession through reusable arithmetic state, with reproducible numerical physics applications.
- Detected languages: Python
- Detected surfaces: cli, library

## How to use this folder
- [INTENT.md](./INTENT.md): what success means and what is explicitly out of scope.
- [ARCHITECTURE.md](./ARCHITECTURE.md): topology, runtime model, data boundaries, and ADR trail.
- [INTERFACES.md](./INTERFACES.md): API/CLI/events/storage contracts and failure behavior.
- [VALIDATION.md](./VALIDATION.md): proof commands, quality gates, and evidence artifacts.
- [SEMANTICS.md](./SEMANTICS.md): state machines, invariants, replay rules, and idempotency.
- [OPERATIONS.md](./OPERATIONS.md): SLOs, monitoring, incident response, and rollout strategy.
- [SECURITY.md](./SECURITY.md): threat model, trust boundaries, auth/authz, and supply-chain posture.

## Canonical `.decapod/` Layout
- `.decapod/data/`: canonical control-plane state (SQLite + ledgers).
- `.decapod/managed/Dockerfile.decapod`: Decapod's project-specific execution image; Decapod runs inside it and may add project build dependencies such as Go, Python, or system packages. Glibc is the default; `--image-profile alpine` selects the GHCR `-alpine`-tagged musl image.
- `.decapod/managed/specs/`: **Living project specs** for humans and agents.
- `Dockerfile` at the project root remains the product application's container image and is the artifact users package and deploy.
- `.decapod/managed/context/`: ignored, current-run deterministic context capsules.
- `.decapod/managed/policy/`: ignored, current-run JIT context policy material; use `.decapod/policy/` for a durable override.
- `.decapod/managed/artifacts/`: ignored, current-run provenance/custody/inventory/diagnostic outputs.
- `.decapod/governance.json`: the sole tracked governance document, with a compact baseline, current plan and trajectory, validation evidence, active claims, explicit unresolved obligations, and cumulative current-PR checkpoints.
- `decapod workspace ensure` seeds the fresh work-branch governance template from the claimed task; repeated calls preserve current work. `decapod govern artifacts begin-pr --id <change> --base-branch <base>` is the explicit recovery boundary. Accepted claims remain recoverable in Git; template generation never supplies successful validation.
- `decapod govern artifacts checkpoint --id <checkpoint> --summary "..." --proof-ref <evidence>` records proof after staging authored work; stage the governance document next and commit both. Publication verifies the complete authored commit range.
- Historical observation sections remain readable as archived evidence; they do not authorize current work.
- `.decapod/managed/artifacts/inventory/`: deterministic release inventory.
- `.decapod/managed/artifacts/diagnostics/`: opt-in diagnostics artifacts.
- `.decapod/workspaces/`: isolated todo-scoped git worktrees.

## Specification Status
- This directory is a set of reviewable contracts, not a generated status dump.
- Generated facts are bounded to the marked attestation/capability blocks; prose
  outside those blocks is authored project intent and must be reviewed like code.
- Each change should update the spec that owns its changed behavior and record
  the proof expected for that change.

## Per-Change Maintenance Loop
1. Identify the changed intent, component, interface, state transition, proof
   obligation, operational procedure, or trust boundary.
2. Update the owning spec before implementation is considered complete.
3. Record compatibility, migration, rollback, and evidence consequences.
4. Run the validation gates and refresh only the Decapod-owned attestation and
   manifest fields.
5. Review the resulting diff as part of the change; a fingerprint-only refresh
   is not a substitute for an authored contract update.

## Day-0 Onboarding Checklist
- [ ] Replace all placeholders in all 8 spec files.
- [ ] Confirm primary user outcome and acceptance criteria in [INTENT.md](./INTENT.md).
- [ ] Confirm topology and runtime model in [ARCHITECTURE.md](./ARCHITECTURE.md).
- [ ] Document all inbound/outbound contracts in [INTERFACES.md](./INTERFACES.md).
- [ ] Define validation gates and CI proof surfaces in [VALIDATION.md](./VALIDATION.md).
- [ ] Define state machines and invariants in [SEMANTICS.md](./SEMANTICS.md).
- [ ] Define SLOs, alerting, and incident process in [OPERATIONS.md](./OPERATIONS.md).
- [ ] Define threat model and auth/authz decisions in [SECURITY.md](./SECURITY.md).
- [ ] Ensure architecture diagram, docs, changelog, and tests are mapped to promotion gates.
- [ ] Run all validation/test commands and attach evidence artifacts.
