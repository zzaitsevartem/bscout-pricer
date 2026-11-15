import json
import subprocess
from pathlib import Path
from uuid import uuid4

root = Path('.unlazy/stage-one-completion/evidence')
services = []
try:
    for service, image, port, extra in [
        ('pg', 'postgres:16-alpine', '5432', ['-e', 'POSTGRES_PASSWORD=isolated-test-password', '-e', 'POSTGRES_DB=bscout_test']),
        ('redis', 'redis:7-alpine', '6379', []),
    ]:
        name = f'bscout-develop-one-{service}-{uuid4().hex[:10]}'
        cid = subprocess.check_output(['docker', 'run', '--rm', '-d', '--name', name,
                                      '-p', f'127.0.0.1::{port}', *extra, image], text=True).strip()
        services.append({'service': service, 'name': name, 'id': cid})
        mapped = subprocess.check_output(['docker', 'port', cid, f'{port}/tcp'], text=True).strip()
        services[-1]['port'] = int(mapped.rsplit(':', 1)[1])
    (root / 'services.json').write_text(json.dumps(services, indent=2))
    print(json.dumps([{'service':s['service'],'name':s['name'],'port':s['port']} for s in services]))
except BaseException:
    for service in services:
        subprocess.run(['docker', 'rm', '-f', service['id']], capture_output=True)
    raise
