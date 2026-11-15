# Gates: develop-one stage 1 completion

Scope: reconcile five stage-one acceptance items with current implementation and captured evidence. No gate is marked complete merely because a direct command passed; automatic records remain pending until the exact CHECK is inspected and approved.

- [x] G1: Focused validation and matching regressions pass without skips.
  CHECK: /private/tmp/bscout-develop-one-venv/bin/python ../.unlazy/stage-one-completion/evidence/run_backend_checks.py tests/unit/test_validation_redaction.py tests/unit/test_matching_rematch.py -q
  EXPECT: BACKEND_VERIFIED_NO_SKIPS
  CWD: /Users/zzaitsevartem/Desktop/projects/bscout/backend
  EVIDENCE: automatic-evidence=v1; definition-sha256=bea7dd5620573351b625906bf43c25eb68f89c7ff69e0f6830f1bc1f8d912063; exit=0; EXPECT=matched; output-sha256=0fa435bd11d396cf45c120af29c8fa87cb6990eb400980f1b560ed10c8d2d904; output-bytes=619; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/backend; path=26d5e060990c/35 entries

- [x] G2: Full backend unit suite passes without skips on current code.
  CHECK: /private/tmp/bscout-develop-one-venv/bin/python ../.unlazy/stage-one-completion/evidence/run_backend_checks.py tests/unit -q
  EXPECT: BACKEND_VERIFIED_NO_SKIPS
  CWD: /Users/zzaitsevartem/Desktop/projects/bscout/backend
  EVIDENCE: automatic-evidence=v1; definition-sha256=aa830c02ecf22af1f6b566739e4c6e876b6d45cddb1ea743b4039a9403b361fa; exit=0; EXPECT=matched; output-sha256=f76661a524c40a85290f9028941d91a3d354baca7d5563cf3c1325ae55601b62; output-bytes=2240; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/backend; path=26d5e060990c/35 entries

- [x] G3: Real Redis multi-process rate-limit integration passes without skips.
  CHECK: /private/tmp/bscout-develop-one-venv/bin/python ../.unlazy/stage-one-completion/evidence/run_backend_checks.py tests/integration/test_rate_limit_live_redis.py -q
  EXPECT: BACKEND_VERIFIED_NO_SKIPS
  CWD: /Users/zzaitsevartem/Desktop/projects/bscout/backend
  EVIDENCE: automatic-evidence=v1; definition-sha256=fb99e6d57262b796d37a743cf0a8d524cfa9f6b9b666cbac05057d92b5ef6c82; exit=0; EXPECT=matched; output-sha256=9aef13989d9ed724d28a12c81150a07ceb30e57709b4245b15fc5c635a4bb247; output-bytes=1035; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/backend; path=26d5e060990c/35 entries

- [x] G4: Auth integration suite passes without skips against the disposable task DB.
  CHECK: python3.11 .unlazy/stage-one-completion/evidence/run_auth_integration.py
  EXPECT: AUTH_INTEGRATION_VERIFIED_NO_SKIPS
  CWD: /Users/zzaitsevartem/Desktop/projects/bscout
  EVIDENCE: automatic-evidence=v1; definition-sha256=b092b8c0ec260b67f3eb640d0ba2d79a00b8f2aa06ad0b76449c9fc812d066f9; exit=0; EXPECT=matched; output-sha256=8d783e56a719eac3bbf7f69fa0d03ae579df2b93736e04916477fc2139a2dd03; output-bytes=35; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=26d5e060990c/35 entries

- [x] G5: Current frontend tree passes tests, lint, and production build.
  CHECK: npm test && npm run lint && npm run build && echo FRONTEND_COMPATIBLE
  EXPECT: FRONTEND_COMPATIBLE
  CWD: /private/tmp/bscout-develop-one-frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=af3f11d9c3a1a1f7961961aecde9d062b278f4aa0bc60fe1b925210303aa10b1; exit=0; EXPECT=matched; output-sha256=aa2c81820f626a2ca23eec0969a2882fc6805bbc83efdb563ef63b2435828473; output-bytes=3143; shell=/bin/sh; cwd=/private/tmp/bscout-develop-one-frontend; path=26d5e060990c/35 entries

- [x] G6: Current advisories and configuration-dependent residual risk are accurately assessed.
  EVIDENCE: Root reconciled fresh npm/pip artifacts and Terra review: npm zero; two unique Python advisories OPEN, algorithm configurable with HS256 default, production config uninspected. Report gptaudits/88.md explicitly states conditional applicability.

- [x] G7: A fresh limited Profi import reaches persisted offers, matching, catalog/search, and browser source link; selected registration plan returns to checkout without granting paid access.
  EVIDENCE: Root reconciled Luna direct-checks and independent Terra review: 55 response hashes, parser replay10/10, DB10/10, API positive/negative checks and browser exact URL+trial/no payment assertions. Limited pilot with six404s; harness-only label distinguished.

- [x] G8: Complexity inventory is recorded and scope constraints are respected.
  EVIDENCE: Root reviewed complexity-audit.md and git diff/status: no justified cut, no unrelated product changes, three code/test files only; commit/deploy/stage2 not performed. Only disposable test resources used.
