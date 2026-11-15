# Verification contract r1

Live task plan: docs/plan/MASTERPLAN.md. This file is a dispatch/acceptance contract only.

Contract: C1 rate limit/proxy/Redis → root G1/G1R; C2 secret errors → G2; C3 dependencies/compatibility → G3/G3B/G3C; C4 live Profi zapchasti provenance and full chain → G4; C5 selected registration plan without granting access → G5. Stage 2 forbidden until owner confirms. No commits or publication. Main agent owns implementation/integration. Reviewer reads current diffs, owns only review.md, does not run checks or touch code/env.

Tree:
- 1 develop-one acceptance GATES.md
  - 1.1 security review integration gates/node-1.1.md
    - 1.1.1 independent review gates/leaf-1.1.1.md

| Leaf | Owns | Needs | Tier | Planned wave | State |
|---|---|---|---|---|---|
| 1.1.1 | .unlazy/develop-one/review.md | - | judgment | review-1 | VERIFIED |

Ownership sets compared: exact equal one-path set. Reviewer requested bscout_reviewer (Sol/medium by skill). Main agent independently validates findings and records resolution; reviewer does not certify runnable root gates.
