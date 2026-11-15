# Gates: develop-one, этап 1

OWNS: backend/**, frontend/**, docs/plan/MASTERPLAN.md, gptaudits/80.md, gptaudits/81.md

Scope: Пять задач этапа 1 develop-one.md; живой план только docs/plan/MASTERPLAN.md. Этап 2 запрещён до подтверждения владельца.

- [x] G1: Rate limit покрывает маршруты, proxy, изоляцию, конкуренцию, Redis outage и восстановление.
  CHECK: /private/tmp/bscout-develop-one-venv/bin/python ../.unlazy/develop-one/run_backend_checks.py tests/unit/test_rate_limit.py tests/unit/test_rate_limit_redis.py tests/unit/test_rate_limit_policy.py -q
  EXPECT: BACKEND_VERIFIED_NO_SKIPS
  CWD: backend
  EVIDENCE: automatic-evidence=v1; definition-sha256=f78e981095a708d7bc22ada656b60c28d862e40515ef7de7faa011ed81aee5cf; exit=0; EXPECT=matched; output-sha256=042bb26aa0dc9036b8be6c1ccb9730d8088e19a12a30374c437682de895ff85e; output-bytes=1808; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/backend; path=26d5e060990c/35 entries

- [x] G2: HTTP422 не возвращает чувствительные значения и сохраняет ошибки полей.
  CHECK: /private/tmp/bscout-develop-one-venv/bin/python ../.unlazy/develop-one/run_backend_checks.py tests/unit/test_validation_redaction.py -q
  EXPECT: BACKEND_VERIFIED_NO_SKIPS
  CWD: backend
  EVIDENCE: automatic-evidence=v1; definition-sha256=a47c1bd26b2a4842f4e09973b7de0ffc8ec130b367fd058dcea0cc1c376cc372; exit=0; EXPECT=matched; output-sha256=f676eb2c2dbaecaccc18836513d598a7853635168bdda872d0bb47c182d29437; output-bytes=619; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/backend; path=26d5e060990c/35 entries

- [x] G3: Актуальные backend/frontend advisories проверены, исправления совместимы, остаточные findings обоснованы.
  EVIDENCE: npm-after.json total=0; pip-after.json remaining python-jose/ecdsa advisories assessed in dependency-findings.md, no fixed release and HS256 explicit algorithm limits applicability; G3B/G3C independently reverified after review fixes, 84 isolated auth integration tests passed. Review report review.md accepted; no remaining actionable P2.

- [x] G4: Согласованный живой источник проходит import → offers → каталог → поиск → карточка → ссылка, происхождение сохранено.
  EVIDENCE: Owner selected Profi zapchasti. profi-browser-live.json contains 10 freshly fetched offers with HTML fingerprints; accept_profi.py persisted raw provenance, 10 auto matches and 10 catalog/search rows in own PostgreSQL16. profi-chain.json, browser-acceptance.json, screenshots profi-search.png/profi-product.png inspected. Exact source URL confirmed in both UI screens against fetched offer. Four stale sitemap URLs returned 404; bounded pilot, not a full-store crawl.

- [x] G5: Регистрация сохраняет валидный выбранный тариф и возвращает к оформлению без выдачи доступа.
  CHECK: npm exec vitest run src/app/register/page.test.tsx && echo REGISTER_VERIFIED
  EXPECT: REGISTER_VERIFIED
  CWD: /private/tmp/bscout-develop-one-frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=1d55b31757abacfdfbfe24aeefc3f6c87e7a20d81f9841016c612fb68a08c41a; exit=0; EXPECT=matched; output-sha256=a659bb1cabd80725f637ad2572eea8a7e29f17e1218eafc80285e8d73a21ca0d; output-bytes=245; shell=/bin/sh; cwd=/private/tmp/bscout-develop-one-frontend; path=26d5e060990c/35 entries

- [x] G1R: Реальный Redis обеспечивает общий атомарный бюджет четырём процессам и освобождает окно.
  CHECK: /private/tmp/bscout-develop-one-venv/bin/python ../.unlazy/develop-one/run_backend_checks.py tests/integration/test_rate_limit_live_redis.py -q
  EXPECT: BACKEND_VERIFIED_NO_SKIPS
  CWD: backend
  EVIDENCE: automatic-evidence=v1; definition-sha256=a12ff9a0f5d40902b85313d3b30f13d73a03acb1985cfad8393b7e8667f8b3d3; exit=0; EXPECT=matched; output-sha256=00d5d0c41487e84c4612dc77609e2322be124ae296c539ebb228f7ceb0825057; output-bytes=1035; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/backend; path=26d5e060990c/35 entries

- [x] G3C: Обновлённый frontend проходит регрессионные тесты, lint и production build в копии без .env.
  CHECK: npm test && npm run lint && npm run build && echo FRONTEND_COMPATIBLE
  EXPECT: FRONTEND_COMPATIBLE
  CWD: /private/tmp/bscout-develop-one-frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=af3f11d9c3a1a1f7961961aecde9d062b278f4aa0bc60fe1b925210303aa10b1; exit=0; EXPECT=matched; output-sha256=37da2fe66d6384d532160e53d6cf97560fa9dd9cd95673b47c5542f54186476e; output-bytes=3143; shell=/bin/sh; cwd=/private/tmp/bscout-develop-one-frontend; path=26d5e060990c/35 entries

- [x] G3B: Backend unit suite на обновлённых зависимостях проходит без пропусков.
  CHECK: /private/tmp/bscout-develop-one-venv/bin/python ../.unlazy/develop-one/run_backend_checks.py tests/unit -q
  EXPECT: BACKEND_VERIFIED_NO_SKIPS
  CWD: backend
  EVIDENCE: automatic-evidence=v1; definition-sha256=27b7f3b366ddec8aa38754e33bbe8691d2af40b84922ac821bd70a6b273f1306; exit=0; EXPECT=matched; output-sha256=c3206d2812a1b6bf0ae576d1f75b9cf015c7293f63154f0b03e4eb469365dc88; output-bytes=2240; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/backend; path=26d5e060990c/35 entries
