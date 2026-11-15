# Plan: finish develop-one stage 1

Scope: stage-one-completion
Depth: tree 1
Mode: sequential implementation then independent verification

## Contract

- Interfaces: retain FastAPI 422 `detail` entries with `loc`, `type`, and safe, useful `msg`; the legacy `.unlazy/develop-one/GATES.md` remains the five-item acceptance ledger.
- Ownership: Luna owns `backend/src/middleware/validation.py`, `backend/tests/unit/test_validation_redaction.py`, `.unlazy/stage-one-completion/evidence/**`, and `gptaudits/88.md`; Terra owns `.unlazy/stage-one-completion/review.md` and `.unlazy/stage-one-completion/gates/leaf-review.md` only.
- Dependencies: review waits for Luna's fix, self-checks, and fresh acceptance evidence.
- Host launch mode: sequential native subagent task; no parallel wave.
- Wave policy: one implementation leaf followed by one independent review leaf.
- Toolchain: existing Python 3.11 isolated test env and preconfigured frontend copy; use no real `.env`; all writes to databases use newly created isolated services.
- Conventions: minimum shared 422 sanitizer and focused regression. Do not change payment or stage-two behavior.
- Manual review: Terra reviews the focused diff and evidence; browser-visible source URL and genuine imported-offer lineage require artifact inspection.

## Current contract inventory

Contract revision: 3. User added a lightweight repo-wide complexity inventory and behavior-preserving simplification requirement. Full backend unit rerun exposed a stale AsyncMock result setup in a matching regression test; add only the fixture path to implementation ownership and verify the existing test's intended production behavior.

| ID | Required outcome | Owner | Observation | Disposition | Revision |
|---|---|---|---|---|---|
| C1 | Rate limits cover routes, proxy, identity, Redis outage and shared-process operation | Luna | existing gates G1/G1R plus fresh test evidence | ACTIVE | 1 |
| C2 | 422 responses and auth validation logs do not disclose input secrets while retaining useful errors | Luna | inherited gate G2 and regression review | ACTIVE | 1 |
| C3 | Current dependency advisories, lock consistency and compatibility are documented | Luna | inherited G3/G3B/G3C plus current audit artifacts | ACTIVE | 1 |
| C4 | A new, agreed Profi offer traverses live fetch → persistence/provenance → matching → catalog/search → card/source URL | Luna | G4 evidence and browser artifact | ACTIVE | 1 |
| C5 | Valid registration plan returns to checkout without granting paid access | Luna | inherited G5 and prior browser evidence where source is unchanged | ACTIVE | 1 |
| C6 | No deployment, commit, real `.env` read, stage-two work, or edits outside declared ownership | Luna/Terra | root handoff review | ACTIVE | 1 |
| C7 | Lightweight repo-wide over-engineering inventory; simplify only useful, verified findings without weakening behavior or broadening product scope | Luna | `.unlazy/stage-one-completion/evidence/complexity-audit.md`, Terra review | ACTIVE | 2 |
| C8 | Existing matching regression unit test remains valid for the real SQLAlchemy result shape | Luna | leaf-impl:I7 and backend unit rerun | ACTIVE | 3 |

## Tree

- 1 Completion ........ GATES.md
  - 1.1 Independent verification .... gates/node-1.1.md
    - 1.1.1 Implementation + self-check .... gates/leaf-impl.md
    - 1.1.2 Terra review .................... gates/leaf-review.md

## Leaf dispatch table

| Leaf | Owns | Needs | Tier | Planned wave | State |
|---|---|---|---|---|---|
| 1.1.1 | backend/src/middleware/validation.py, backend/tests/unit/test_validation_redaction.py, backend/tests/unit/test_matching_rematch.py, .unlazy/stage-one-completion/evidence/** | - | judgment | 1 | IN-FLIGHT — implementation and direct checks complete; formal gate verification awaits inspected user approval |
| 1.1.2 | .unlazy/stage-one-completion/review.md, .unlazy/stage-one-completion/gates/leaf-review.md | 1.1.1 | judgment | 2 | DONE — Terra review complete; root reconciliation awaits formal gate verification |
