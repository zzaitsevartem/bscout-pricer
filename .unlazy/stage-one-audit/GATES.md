# Gates: stage-one audit

Scope: reconcile both independent audits against all five current stage-one acceptance items and report any unmet item honestly.

- [x] G1: Every stage-one criterion has a verdict, evidence, and explicit distinction between defect and evidence gap.
  EVIDENCE: G1 rate limit — PASS on prior same-day route inventory and test evidence; Terra reran 75 focused unit tests, 0 skipped. Live Redis multi-process evidence exists in prior GATES, not repeated in this audit. G2 validation — FAIL: the current 422 handler reflects a malformed email fragment; reproduced by Terra. G3 dependency security/compatibility — PASS on same-day npm audit (30→0), backend audit (26→3 records representing two justified advisories), compatibility tests/build/lint from the prior run; residual python-jose and ecdsa findings remain documented, and production config was not reviewed. G4 real-source chain — UNVERIFIED on current code: full 10-offer Profi pilot predated matching/extractor/comparison changes; current-code search/detail checks cover existing offers only. G5 selected plan — PASS on focused 10/10 registration/subscription tests in an isolated current-code copy and prior browser acceptance; paid access was not granted. Scope counts: 3 pass, 1 fail, 1 unverified. Stage 1 is not complete.

- [x] G2: Stage 2, product edits, env-file reads, and commits remain outside the audit.
  EVIDENCE: Confirmed with Terra and this audit; no product edits, real environment-file reads, commits, deployment, or stage-two checks.
