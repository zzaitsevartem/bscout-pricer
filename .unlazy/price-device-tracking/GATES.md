# Gates: price and device tracking

OWNS: backend/**, frontend/**, DESIGN.md, docs/**, gptaudits/76.md

Scope: revision 3 — device preview card must share the visual structure of the price card, with search outside; also preserve meaningful red/green price signals, mirror device card left of its copy, fix live device API/schema, and advertise Advanced device tracking in every current tariff feature list. Previous revision evidence remains in logs/formal-gates.log and audit 75.

- [x] G1: Price presentation distinguishes zero, drop, increase and unavailable data; tracked items navigate to their product
  CHECK: npx vitest run src/widgets/authorizedHome/ui/TrackingOverview.test.tsx src/widgets/authorizedHome/ui/DeviceTracking.test.tsx 'src/app/devices/[model_key]/DevicePage.test.tsx' && echo TRACKING_UI_VERIFIED
  EXPECT: TRACKING_UI_VERIFIED
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=e238e9567f590bfa384941d6c4ff063ddb356580f45a0e6ae3d64296d210d864; exit=0; EXPECT=matched; output-sha256=cc05090f23ea4a5b2d5b36613dd88c0735e47b70cf29ec54c71b6b0c274a2f42; output-bytes=688; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=6b31f4bc57ea/35 entries

- [x] G2: Device subscriptions persist, enforce Advanced server-side and detect new parts without duplicate notifications
  CHECK: cd /private/tmp && TEST_DATABASE_URL='postgresql+asyncpg://postgres:isolated@127.0.0.1:60754/bscout_test' POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=60754 POSTGRES_USER=postgres POSTGRES_PASSWORD=isolated POSTGRES_DB=bscout_test REDIS_HOST=127.0.0.1 REDIS_PORT=60772 PYTHONPATH=/Users/zzaitsevartem/Desktop/projects/bscout/backend /Users/zzaitsevartem/Desktop/projects/bscout/backend/venv/bin/python -m pytest /Users/zzaitsevartem/Desktop/projects/bscout/backend/tests/integration/test_tracking_api.py -q && echo TRACKING_API_VERIFIED
  EXPECT: /^(?![\s\S]* skipped)[\s\S]*\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=07d5c00fbae439c1dfedcbb78535ad89107e1db3b895027d90b7a6a2b2730128; exit=0; EXPECT=matched; output-sha256=e6004633db4d3e577879af14465e366852b094d30012580e8f597ffd2efd63a5; output-bytes=646; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=6b31f4bc57ea/35 entries

- [x] G3: Separate device block is hidden outside active Advanced and supports add/remove and device navigation
  EVIDENCE: Advanced visibility and device operations verified by component and live QA tests.

- [x] G4: Luna independently reviews Terra test output and Terra resolves every relevant failure
  EVIDENCE: Luna reviewed final test logs and formal results, failures corrected by Terra.

- [x] G5: Migration, scoped integration and frontend static checks pass on final changes
  EVIDENCE: 52 backend integration, 202 frontend tests, 18 targeted tests; lint, Ruff, TypeScript, isolated build and migration passed.

- [x] G6: Data refresh diagnosis, senior simplification review and session audit reflect measured evidence
  EVIDENCE: Live stale backend diagnosed and updated; audit 76 records review and limitations.

- [x] G7: Only scoped changes are committed and pushed on the requested dated branch
  EVIDENCE: Commit dc21b45 pushed to origin/bscout/tracking-ui-tariffs-fix-2026-11-13.

- [x] G8: Every current tariff feature surface and public plan contract includes device tracking for Advanced only
  EVIDENCE: Luna reviewed current tariff surfaces and API; advanced-only capability tested.

- [x] G9: Authenticated live API and desktop/mobile interface load devices and support add/remove/navigation after schema and runtime update
  EVIDENCE: Authenticated QA added, navigated and removed iPhone 15; desktop/mobile checked.

- [x] G10: Price rises remain red and drops render green; zero is visibly neutral and device layout mirrors price layout on desktop
  EVIDENCE: QA computed red/green, neutral zero; mirrored desktop positions and mobile checked.

- [x] G11: Device preview card matches the price card shell, dark header, ivory rows, typography and spacing; search controls sit outside the card
  EVIDENCE: Shared card and row component; live measured matching shell, header and row sizes; search outside card.
