import json
import os
import socket
import sys
from pathlib import Path
import pydantic_settings.sources
pydantic_settings.sources.DotEnvSettingsSource._read_env_files = lambda self: {}
root = Path.cwd()
services = {s['service']:s for s in json.loads((root/'.unlazy/stage-one-completion/evidence/services.json').read_text())}
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
(root/'.unlazy/stage-one-completion/evidence/runtime.json').write_text(json.dumps({'backend_port': port}))
os.environ.update(POSTGRES_HOST='127.0.0.1', POSTGRES_PORT=str(services['pg']['port']), POSTGRES_USER='postgres',
                  POSTGRES_PASSWORD='isolated-test-password', POSTGRES_DB='bscout_test', REDIS_HOST='127.0.0.1',
                  REDIS_PORT=str(services['redis']['port']), JWT_SECRET_KEY='isolated-tests-random-secret-for-develop-one-only')
sys.path.insert(0, str(root/'backend'))
import uvicorn
uvicorn.run('src.main:app', host='127.0.0.1', port=port, proxy_headers=False)
