# Independent review: stage one

## Directly verified

- Current sanitizer builds messages from fixed strings rather than Pydantic `msg`; malformed email `x@private-token💥.com` and invalid nested password/email structures no longer echo the marker. Targeted validation and matching tests: 8 passed, no skips. Full backend unit suite: 487 passed, no skips. Ruff on the three changed files: clean. The matching test keeps its original assertions, with an async execute mock returning an object whose `scalars()` is synchronous, matching SQLAlchemy.
- `loc` remains unchanged by the sanitizer. A synthetic route using `dict[str,int]` reflects an arbitrary dictionary key in `loc`. The current auth schemas have no forbidden extras or discriminated unions; no request schema with validated `dict[str,int]` was found. This is a future general-handler limitation, not a demonstrated leak on an existing route. The actual malformed-email bug is fixed.
- In `/private/tmp/bscout-develop-one-frontend`, `npm exec vitest run src/app/register/page.test.tsx src/app/subscription/page.test.tsx` passed 10 tests; SHA256 of both page and both test files matched checkout. Checkout-local node_modules were stale (Vitest 2.1.9/Next 14.2.35 versus requested Vitest ^4.1.11/Next ^15.5.29), so their failed direct run was not counted as product failure.
- Fresh source snapshot timestamp 2026-11-15T19:28:16.611557Z: 55/55 saved response hashes independently verified, all 10 offer URLs correspond to captured response URLs. Independently parsing those ten saved HTML pages with current `ProfiParser.parse_product_html` reproduced SKU/title/URL/retail/stock and original raw fields 10/10. Fetch harness uses existing parser with runtime-only Chromium-to-installed-Chrome channel override. Six source URLs returned HTTP 404; this is a limited 10-offer pilot, not a full store crawl.
- Read-only SQL and HTTP against the task-created isolated database/API after Luna restored the fresh snapshot: 10 rows, 10 auto-matched; all 10 match snapshot SKU/title/price/URL/store and timestamp. All 10 original raw dictionaries equal snapshot when the additional `acceptance_provenance` field is removed. That field is inserted by the acceptance harness to mark its run; it is not emitted by the production parser. Native provenance persists via store id/slug, SKU, URL and parser raw. Catalog and iPhone search returned 200/10; product detail returned 200 with the URL from catalog and snapshot; nonsense search returned 200/0. No second source fetch was necessary.
- Inspected current browser screenshots: product page shows Profi, 199 rubles, no stock, and store button; subscription page shows trial access and text that Advanced was selected. Inspected browser script and JSON: it checks exact snapshot URL in search/detail and target=_blank, successful advanced redirect, trial API status and no payment POST. Screenshots alone do not prove href, HTTP state, or absence of requests; these are script assertions.

## Cross-agent evidence, not independently rerun

- Luna reports auth integration 84 passed, no skips. Fresh npm audit JSON records zero advisories; pip audit JSON records python-jose PYSEC-2026-4298 and duplicate ecdsa PYSEC-2026-1325 entries, no fix versions. Their applicability rationale and manifest compatibility require parent reconciliation.
- Inherited Redis multi-process checks and frontend full build were not rerun by this reviewer. Some prior gate checks require explicit inspected approval. `gate-check --scope stage-one-completion --status` on review returned 19 unchecked gates; this is not independent gate execution or acceptance. Parent must reconcile current evidence and approval requirements before claiming formal completion.

No product code was changed in review. Review used ponytail and code-simplification principles; no necessary simplification of the scoped sanitizer was identified. The wider complexity audit is Luna's responsibility.

## Current acceptance status

1. Rate limits: policy and unit tests independently reviewed/passed; real Redis multiprocess evidence awaits parent confirmation and any required inspected approval.
2. Validation: prior actual email leak fixed in directly tested cases; general future `loc` caveat above. Auth integration independently reported by Luna.
3. Dependencies: current audit artifact reviewed, remaining two unique advisories have no published fix in that artifact; compatibility and mitigation rationale require parent reconciliation.
4. Live Profi source: current limited 10-offer chain independently cross-checked as described; source returned six 404s. This is not a complete crawl.
5. Selected plan: frontend component tests independently passed on identical files; browser script and screenshot corroborate Advanced selection, trial access and no payment POST, but browser execution itself was Luna's.

Reviewed current SHA256:

- `backend/src/middleware/validation.py`: d2509e3097e8640db81224d2e87e7ad5baaec68a631d700e99ffff05b20caf5c
- `backend/tests/unit/test_validation_redaction.py`: 684e76f65b5b926ece6e69614141976067ff86c9f7049f3a1352239d86e8e3d0
- `backend/tests/unit/test_matching_rematch.py`: 768e99a1cd14d8f848263e508b26356adb5226abf8fb9ab3e95ea66579585761
- `backend/src/modules/parser/service/parsers/profi.py`: 1da6b5479994cf2a80458e5eafcab15e29cc2ea49cfdc1617883e1af97851a24
- `backend/src/modules/parser/service/parser_service.py`: b5d7b03d4f7d902387c4cb96726319bc28ef25c7c5d47eb086e4cf76825fac20
- `backend/src/modules/products/service/matching_service.py`: d63ce02493b80d33897594d4dbddc73adec3993c779346b616b79a858bde4bea
- `backend/src/modules/products/service/comparison_service.py`: 4170caf08a2bacd81d20d144d4acced5246f4020ccc2611144cd4183b9c24bd0

These are post-review fingerprints, not independently recorded hashes from the start of the original fetch.

## Independent dependency-path review

`backend/src/config.py` sets `jwt_algorithm` to HS256 by default, but it is configurable; the application is not HS256-only. `backend/src/modules/auth/service/auth.py` signs with that setting and calls `jwt.decode` with `[settings.jwt_algorithm]`, a single configured algorithm. No direct ECDSA/ES256 use was found by search in `backend/src`; changing the configured algorithm can change the signing path. The advisory applicability argument is therefore conditional on the actual deployment retaining HS256 and using an appropriate secret, not a claim that the packages or every configuration are safe. Real production configuration was not inspected. Both upstream advisories remain unresolved.

## Final reconciliation of reported evidence

Reviewed Luna's `evidence/direct-checks.md` and `evidence/complexity-audit.md`: current direct reports include 71 rate-limit unit cases, one four-process Redis case, 84 auth integration cases, frontend 224 tests/42 files and successful lint/build. The Redis, auth integration and full frontend checks were not independently rerun by Terra; they are cross-agent evidence. The complexity report is a targeted inventory, not a full line-by-line audit, and found no justified cut. Current changed-file SHA256 matches the post-review fingerprints above. On the evidence available, all five requested items have functional evidence, subject to the documented source pilot scope, configurable JWT algorithm, unresolved dependency advisories, and unverified production environment. This is manual reconciliation and does not certify Unlazy automatic gates or bypass inspected approval requirements.

## Frontend compatibility correction

The earlier full run of 220 tests/41 files is withdrawn as current-checkout evidence because the isolated copy was stale. Luna synchronized five tracked paths and reported a fresh run of 224 tests/42 files, lint clean, and Next build passed. Reviewed `evidence/frontend-source-hashes.json`: it records 266/266 tracked source/config/test/lock files equal, zero missing/mismatch, excluding generated `next-env.d.ts`, `.env*`, and build/dependency directories. This manifest and complete rerun are Luna-provided evidence, not independently re-executed in this review. The earlier independently run 10 focused tests had matching hashes for their four specific files, but do not establish equality of the full checkout.
