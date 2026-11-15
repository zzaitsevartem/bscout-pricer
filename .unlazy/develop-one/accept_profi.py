import asyncio
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pydantic_settings.sources
pydantic_settings.sources.DotEnvSettingsSource._read_env_files = lambda self: {}
ROOT = Path.cwd()
services = {s['service']: s for s in json.loads((ROOT / '.unlazy/develop-one/services.json').read_text())}
os.environ.update(POSTGRES_HOST='127.0.0.1', POSTGRES_PORT=str(services['pg']['port']),
                  POSTGRES_USER='postgres', POSTGRES_PASSWORD='isolated-test-password', POSTGRES_DB='bscout_test',
                  REDIS_HOST='127.0.0.1', REDIS_PORT=str(services['redis']['port']),
                  JWT_SECRET_KEY='isolated-tests-random-secret-for-develop-one-only')
sys.path.insert(0, str(ROOT / 'backend'))
import httpx
from sqlalchemy import select
import src.db_metadata
from src.database import Base, engine, async_session_factory
from src.modules.catalog.service.seed import seed_all
from src.modules.parser.service.base import ParseResult
from src.modules.parser.service.parser_service import ParserService
from src.modules.products.service.matching_service import MatchingService
from src.modules.products.model.product import StoreOffer
from src.modules.stores.model.store import Store
from src.main import app
from src.modules.cache.service.redis_cache import close_redis

async def main():
    snapshot = json.loads((ROOT / '.unlazy/develop-one/profi-browser-live.json').read_text())
    assert snapshot['offers'] and snapshot['source'] == 'profi'
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_factory() as db:
        await seed_all(db)
        store = (await db.execute(select(Store).where(Store.slug == 'profi'))).scalar_one()
        for row in snapshot['offers']:
            for field in ['price_retail', 'price_opt', 'price_old']:
                if row[field] is not None:
                    row[field] = Decimal(row[field])
            row['raw']['acceptance_provenance'] = {'source': 'profi', 'section': 'zapchasti',
                                                  'fetched_at': snapshot['fetched_at'],
                                                  'snapshot': 'profi-browser-live.json'}
            await ParserService.upsert_offer(db, store.id, ParseResult(**row))
        await db.flush()
        stats = await MatchingService.match_all(db, only_unmatched=True)
        await db.commit()
        offers = (await db.execute(select(StoreOffer))).scalars().all()
        assert len(offers) == 10
        assert all(o.raw['acceptance_provenance']['source'] == 'profi' for o in offers)
        matched = [o for o in offers if o.product_id is not None]
        assert matched
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://testserver') as client:
        registration = await client.post('/api/auth/register', json={
            'email': 'profi-acceptance@example.com', 'full_name': 'Profi acceptance',
            'password': 'test-only-long-password-123',
        })
        assert registration.status_code == 201, registration.text
        client.headers['Authorization'] = 'Bearer ' + registration.json()['access_token']
        catalog = await client.get('/api/products/catalog', params={'store': 'profi'})
        assert catalog.status_code == 200, catalog.text
        data = catalog.json()
        assert data['total'] > 0
        item = data['results'][0]
        search = await client.get('/api/products/catalog', params={'q': 'iPhone', 'store': 'profi'})
        assert search.status_code == 200 and search.json()['total'] > 0, search.text
        detail = await client.get(f"/api/products/catalog/{item['id']}")
        assert detail.status_code == 200, detail.text
        assert any(o.url in detail.text for o in matched)
        report = {'source': 'profi', 'section': 'zapchasti', 'saved': len(offers),
                  'matched': len(matched), 'matching': stats, 'catalog': data,
                  'search': search.json(), 'detail': detail.json(), 'source_errors': snapshot['errors']}
        (ROOT / '.unlazy/develop-one/profi-chain.json').write_text(json.dumps(report, default=str, ensure_ascii=False, indent=2))
        print(json.dumps({'saved': len(offers), 'matched':len(matched), 'catalog_total':data['total'], 'search_total':search.json()['total'], 'product_id':item['id']}))
    await close_redis()
    await engine.dispose()

asyncio.run(main())
