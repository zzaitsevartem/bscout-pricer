# Plan: independent audit of develop-one stage 1

Scope: stage-one-audit
Depth: tree 1
Mode: orchestrated, two read-only audit leaves

## Contract

- Interfaces: evidence maps to five acceptance items in `develop-one.md`; distinguish implementation defects from missing or stale evidence.
- Ownership: Luna owns `.unlazy/stage-one-audit/gates/leaf-luna.md`, this PLAN, root `GATES.md`, and final `gptaudits/87.md`; Terra owns `.unlazy/stage-one-audit/gates/leaf-terra.md`. No product files.
- Dependencies: both leaves independent; integration waits for both returns.
- Host launch mode: native agents already launched by parent; no new dispatch wave opened here.
- Wave policy: work is already in flight; do not alter existing `.unlazy/develop-one` ledger.
- Toolchain: read-only source/document inspection and safe, explicitly requested tests; repository root is CWD. Do not read real `.env` files.
- Conventions: report each criterion as pass, defect, or evidence gap. Stage 2 is outside scope.
- Manual review: Luna reconciles documents and evidence chronology; Terra checks current code and tests.

## Current contract inventory

Contract revision: 1.

| ID | Required outcome or constraint | Owner | Observing gate or manual review | Disposition | Revision |
|---|---|---|---|---|---|
| C1 | Rate limits across routes, identity, proxy, multiprocess, Redis behavior, workload policy | Terra | leaf-terra:G1 | ACTIVE | 1 |
| C2 | Validation responses redact sensitive input while retaining useful errors | Terra | leaf-terra:G2 | ACTIVE | 1 |
| C3 | Dependency advisories, lock consistency, compatibility, unresolved findings | Terra | leaf-terra:G3 | ACTIVE | 1 |
| C4 | Agreed real source completes current import-to-UI chain with provenance | Luna + Terra | leaf-luna:G1, leaf-terra:G4 | ACTIVE | 1 |
| C5 | Validated registration plan returns to checkout without granting paid access | Terra | leaf-terra:G5 | ACTIVE | 1 |
| C6 | Preserve authorization boundary: no product edits, env reads, commits, or stage 2 | Luna + Terra | leaf-luna:G2, leaf-terra:G6 | ACTIVE | 1 |

## Tree

- 1 Stage 1 audit ........ GATES.md
  - 1.1 Evidence and implementation review .... gates/node-1.1.md
    - 1.1.1 Code and tests .................... gates/leaf-terra.md
    - 1.1.2 Evidence chronology ................ gates/leaf-luna.md

## Leaf dispatch table

| Leaf | Owns | Needs | Tier | Planned wave | State |
|---|---|---|---|---|---|
| 1.1.1 | .unlazy/stage-one-audit/gates/leaf-terra.md | - | judgment | 1 | IN-FLIGHT |
| 1.1.2 | .unlazy/stage-one-audit/gates/leaf-luna.md | - | judgment | 1 | IN-FLIGHT |
