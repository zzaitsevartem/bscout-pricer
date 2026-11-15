# Gates: implementation and self-check

OWNS: backend/src/middleware/validation.py, backend/tests/unit/test_validation_redaction.py, backend/tests/unit/test_matching_rematch.py, .unlazy/stage-one-completion/evidence/**

Scope: minimal shared 422 sanitizer, regression coverage, and evidence reconciliation. These CHECKs are intentionally pending inspected approval; direct runs documented in `evidence/direct-checks.md` do not populate automatic Unlazy evidence.

- [x] I1: Shared 422 response keeps useful safe field errors and does not echo the submitted malformed email.
  CHECK: /private/tmp/bscout-develop-one-venv/bin/python ../.unlazy/stage-one-completion/evidence/run_backend_checks.py tests/unit/test_validation_redaction.py tests/unit/test_matching_rematch.py -q
  EXPECT: BACKEND_VERIFIED_NO_SKIPS
  CWD: /Users/zzaitsevartem/Desktop/projects/bscout/backend
  EVIDENCE: automatic-evidence=v1; definition-sha256=bea7dd5620573351b625906bf43c25eb68f89c7ff69e0f6830f1bc1f8d912063; exit=0; EXPECT=matched; output-sha256=28fdbd8d593a422c22cffd70c196e283e440c57b92eccc7679d1fbb4af2972e6; output-bytes=619; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/backend; path=26d5e060990c/35 entries

- [x] I2: The focused matching regression remains valid with SQLAlchemy's synchronous `Result.scalars()` API and preserves its original assertions.
  EVIDENCE: Independent Terra code review confirms synchronous SQLAlchemy result mock and all original matching assertions retained; targeted8 and full487 independently passed.

- [x] I3: Current dependency advisory data and conditional residual risk are documented.
  EVIDENCE: Root and Terra reviewed current advisory artifacts and conditional rationale in gptaudits/88.md; both unique advisories remain OPEN.

- [x] I4: Fresh selected Profi source chain, current-code persistence/matching/catalog/search, and browser source URL are supported by captured evidence.
  EVIDENCE: Independent Terra raw HTML hash and parser replay plus DB/API lineage verification documented in review.md; root reconciled chronology including auth fixture reset and snapshot restore.

- [x] I5: Registration plan/checkout behavior and no paid access are evidenced.
  EVIDENCE: Terra inspected browser script/JSON/screenshots and independently passed focused frontend tests; root reconciled refreshed frontend224 and266-file hash comparison. Advanced selection, trial status, zero payment POST.

- [x] I6: Lightweight complexity inventory and scoped simplification result are recorded.
  EVIDENCE: Root reviewed scoped whole-project pattern inventory and independent Terra assessment: no confirmed useful simplification, zero cuts; no speculative refactor.

- [x] I7: Targeted backend tests pass without skips on the current code.
  CHECK: /private/tmp/bscout-develop-one-venv/bin/python ../.unlazy/stage-one-completion/evidence/run_backend_checks.py tests/unit/test_validation_redaction.py tests/unit/test_matching_rematch.py -q
  EXPECT: BACKEND_VERIFIED_NO_SKIPS
  CWD: /Users/zzaitsevartem/Desktop/projects/bscout/backend
  EVIDENCE: automatic-evidence=v1; definition-sha256=bea7dd5620573351b625906bf43c25eb68f89c7ff69e0f6830f1bc1f8d912063; exit=0; EXPECT=matched; output-sha256=4af2d5087b6148acbc5d0ecde9f7d377f2693f1a5c0bbf528fdee46e03bb58eb; output-bytes=619; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/backend; path=26d5e060990c/35 entries
