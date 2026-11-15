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
from src.config import settings
from src.modules.parser.service.parsers.profi import ProfiParser

OUTPUT = Path('../.unlazy/develop-one')

async def main():
    settings.parser_profi_browser_enabled = True
    responses = []
    class RecordedParser(ProfiParser):
        async def _fetch(self, client, url):
            markup = await super()._fetch(client, url)
            if markup:
                fingerprint = hashlib.sha256(markup.encode()).hexdigest()
                responses.append({'url': url, 'sha256': fingerprint, 'bytes': len(markup.encode())})
                target = OUTPUT / 'profi-pages' / (fingerprint + '.html')
                target.parent.mkdir(exist_ok=True)
                target.write_text(markup)
            return markup
    parser = RecordedParser()
    results = []
    error = None
    try:
        results = await asyncio.wait_for(parser.update_catalog(limit=10, section='zapchasti'), 180)
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
    report = {'fetched_at': datetime.now(timezone.utc).isoformat(), 'source': 'profi',
              'section': 'zapchasti', 'limit': 10, 'mode': 'existing browser parser',
              'errors': parser.errors, 'exception': error, 'responses': responses,
              'offers': [asdict(result) for result in results]}
    (OUTPUT / 'profi-browser-live.json').write_text(json.dumps(report, default=str, ensure_ascii=False, indent=2))
    print(json.dumps({'offers': len(results), 'responses': len(responses), 'errors': parser.errors, 'exception': error}, ensure_ascii=False))
    if not results:
        raise SystemExit(1)
asyncio.run(main())
