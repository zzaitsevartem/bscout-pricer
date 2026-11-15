# Gates: device tracking search and notification checks

OWNS: .unlazy/device-tracking-ideas/**, gptaudits/77.md, frontend/src/widgets/ProductSearch/ui/ProductSearchField.tsx, frontend/src/widgets/authorizedHome/ui/DeviceTracking.tsx, frontend/src/widgets/authorizedHome/ui/DeviceTracking.test.tsx, backend/tests/integration/test_tracking_api.py

Scope: Agree and implement consistent device search suggestions, and verify notification flow with Luna-authored and reviewed tests.

- [x] G1: Product change agreed with the user.
  EVIDENCE: User requested consistent search input and suggested results instead of selecting initial proposals.

- [x] G2: Luna authors, reads and runs meaningful notification flow tests and reports results and limits.
  EVIDENCE: Luna reports isolated PostgreSQL and Redis integration test passed (1 passed, 25 deselected); checks sent notification, duplicate scan, owner API and isolation. External delivery and live worker not tested.

- [x] G3: Agreed search change implemented and verified.
  EVIDENCE: Shared search component used for device suggestions; Luna reports 7 component tests passed, root ran 41 search and device component tests; lint, TypeScript and isolated production build passed. Browser visual acceptance not performed.

- [x] G4: Frequently searched models appear in the device field and selection adds the matching device.
  EVIDENCE: Browser confirmed five frequent suggestions; Luna tested click and keyboard, exact catalog model key, correct id and failures.

- [x] G5: Both cards have improved hover and red-accent removal with a custom confirmation; empty devices are centered with the requested text.
  EVIDENCE: Shared row hover and danger buttons implemented; Luna ran confirmation, cancellation and failure tests on both cards; browser checked product dialog and cancellation and centered empty state.
