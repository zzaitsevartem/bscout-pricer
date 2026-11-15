import json
import os
import subprocess
from pathlib import Path

services = {item['service']: item for item in json.loads(Path('.unlazy/develop-one/services.json').read_text())}
env = os.environ.copy()
env['TEST_DATABASE_URL'] = f"postgresql+asyncpg://postgres:isolated-test-password@127.0.0.1:{services['pg']['port']}/bscout_test"
env['POSTGRES_HOST'] = '127.0.0.1'
env['POSTGRES_PORT'] = str(services['pg']['port'])
env['POSTGRES_USER'] = 'postgres'
env['POSTGRES_PASSWORD'] = 'isolated-test-password'
env['POSTGRES_DB'] = 'bscout_test'
env['REDIS_HOST'] = '127.0.0.1'
env['REDIS_PORT'] = str(services['redis']['port'])
env['JWT_SECRET_KEY'] = 'isolated-tests-random-secret-for-develop-one-only'
command = ['/private/tmp/bscout-develop-one-venv/bin/python', '../.unlazy/develop-one/run_backend_checks.py',
           'tests/integration/test_auth_flow.py', 'tests/integration/test_auth_service.py',
           'tests/integration/test_password_reset.py', 'tests/integration/test_oauth.py', '-q']
with Path('.unlazy/develop-one/auth-integration.log').open('w') as log:
    result = subprocess.run(command, cwd='backend', env=env, stdout=log, stderr=subprocess.STDOUT)
raise SystemExit(result.returncode)
