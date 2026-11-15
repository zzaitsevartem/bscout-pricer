import asyncio
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pydantic_settings.sources
pydantic_settings.sources.DotEnvSettingsSource._read_env_files = lambda self: {}
sys.path.insert(0, str(Path.cwd()))
import httpx
from src.modules.parser.service.parsers.profi import ProfiParser

OUTPUT = Path('../.unlazy/develop-one')

async def main():
    responses = []
    async def record(response):
        body = await response.aread()
        responses.append({'url': str(response.url), 'status': response.status_code,
                          'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body)})
        if response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
            target = OUTPUT / 'profi-pages' / (hashlib.sha256(str(response.url).encode()).hexdigest() + '.html')
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(body)
    async with httpx.AsyncClient(follow_redirects=True, event_hooks={'response': [record]}) as client:
        parser = ProfiParser(client=client)
        results = await parser.update_catalog(limit=10, section='zapchasti')
    report = {'fetched_at': datetime.now(timezone.utc).isoformat(), 'source': 'profi',
              'section': 'zapchasti', 'limit': 10, 'errors': parser.errors,
              'responses': responses, 'offers': [asdict(result) for result in results]}
    (OUTPUT / 'profi-live.json').write_text(json.dumps(report, default=str, ensure_ascii=False, indent=2))
    print(json.dumps({'offers': len(results), 'responses': len(responses), 'errors': parser.errors}, ensure_ascii=False))
    if not results:
        raise SystemExit(1)

asyncio.run(main())
