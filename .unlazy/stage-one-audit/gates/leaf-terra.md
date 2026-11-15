# Gates: Terra independent stage-one audit

OWNS: .unlazy/stage-one-audit/gates/leaf-terra.md

These manual gates describe the audit, not acceptance of stage one.

- [x] G1: Assess current rate limiting and evidence for requested scenarios.
  EVIDENCE: backend/src/middleware/rate_limit.py and client_ip.py; isolated backend runner tests/unit/test_rate_limit.py, test_rate_limit_redis.py, test_rate_limit_policy.py plus test_validation_redaction.py: 75 passed, no skip. Redis cross-process live run not repeated in this audit; outage and route-policy unit cases pass. No claim of production proxy configuration validation.
- [x] G2: Assess validation redaction and auth/log evidence.
  EVIDENCE: NEGATIVE: validation.py retains Pydantic msg. An independent in-process FastAPI/ASGI POST using actual RegisterRequest and handler, body {"email":"x@private-token💥.com","full_name":"Name","password":"password-12345"}, returned 422 with msg containing "private-token💥". Expected no sensitive user-supplied fragment in response; actual fragment returned. Password itself was not exposed by this reproduction. Unit suite misses this case. Logs not comprehensively proven safe by this test.
- [x] G3: Assess advisory currency, dependency alignment and compatibility evidence.
  EVIDENCE: No independent online fresh advisory check performed. Frontend checkout node_modules contains Vitest 2.1.9 and Next 14.2.35 while package.json requests ^4.1.11 and ^15.5.29: direct test execution gave 10 environment errors. Previously prepared isolated copy `/private/tmp/bscout-develop-one-frontend` with Vitest 4.1.12 (setup not repeated or independently audited) ran register/subscription tests: 10 passed; four current page/test files have matching SHA256 against copy. This is an environment limitation, not an application defect. Offline npm audit does not establish current advisories.
- [x] G4: Assess live source evidence against current source, including all links in the chain.
  EVIDENCE: Compared current code to 1a98115: later commits changed extractor.py, matching_service.py and comparison_service.py. Prior live chain preceded these changes; no independent fresh end-to-end import through UI performed. Luna should distinguish historical evidence from verification on current code; current full-chain acceptance remains unproven on evidence available to Terra.
- [x] G5: Assess selected plan behavior and negative cases.
  EVIDENCE: register/page.tsx validates basic/advanced, routes only after success; invalid values route to account, registration request omits plan. register and subscription test files passed 10/10 in isolated copy, matching current page/test SHA256; checkout itself not independently exercised by Terra in a real browser.

Commands and observations:

- From backend: `/private/tmp/bscout-develop-one-venv/bin/python ../.unlazy/develop-one/run_backend_checks.py tests/unit/test_rate_limit.py tests/unit/test_rate_limit_redis.py tests/unit/test_rate_limit_policy.py tests/unit/test_validation_redaction.py -q` -> 75 passed, 0 skipped.
- From frontend: `npm exec vitest run src/app/register/page.test.tsx src/app/subscription/page.test.tsx` -> 10 failed because local installed Vitest 2 lacked configured jsdom projects; not a product failure. Same command from `/private/tmp/bscout-develop-one-frontend` -> 10 passed, Vitest 4.1.12. SHA256 current and copied register/subscription page and test files all equal pairwise (`shasum -a 256` comparison).
- Standalone reproduction from backend using the isolated Python environment, with dotenv loading disabled before importing app modules:

```python
import asyncio
import httpx
import pydantic_settings.sources
pydantic_settings.sources.DotEnvSettingsSource._read_env_files = lambda self: {}
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from src.middleware.validation import validation_error_response
from src.modules.auth.schema.auth import RegisterRequest
app = FastAPI()
app.add_exception_handler(RequestValidationError, validation_error_response)
@app.post('/register')
async def register(body: RegisterRequest):
    return {'ok': True}
async def main():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
        r = await c.post('/register', json={'email':'x@private-token💥.com','full_name':'Name','password':'password-12345'})
        print(r.status_code, 'private-token' in r.text, r.text)
asyncio.run(main())
```

Actual: `422 True` and the validation message includes `private-token💥`. Expected: no user-supplied sensitive fragment echoed, while retaining useful form validation. This is a self-contained test app using the same handler and request schema, not a live deployment.

Verdict: NEGATIVE. G1-G5 are audits performed, not five claims of implementation acceptance. G2 is a reproduced defect; G3 and G4 have evidence limitations, not inferred defects; G5 focused tests pass with the declared limitations above. No product changes made.
