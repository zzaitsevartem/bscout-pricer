import json
import os
import sys
from pathlib import Path
import pydantic_settings.sources
pydantic_settings.sources.DotEnvSettingsSource._read_env_files = lambda self: {}
os.environ['JWT_SECRET_KEY']='isolated-tests-random-secret-for-develop-one-only'
sys.path.insert(0,str(Path.cwd()/'backend'))
from src.main import app
from src.middleware.rate_limit import RateLimitMiddleware
from starlette.requests import Request
limiter=RateLimitMiddleware(None)
rows=[]
for path, operations in app.openapi()['paths'].items():
    for method, operation in operations.items():
        if method.upper() not in {'GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS'}:
            continue
        request=Request({'type':'http','path':path,'method':method.upper(),'scheme':'http','headers':[],
                         'query_string':b'', 'client':('192.0.2.1',1)})
        rows.append({'path':path,'method':method.upper(),'operation':operation['operationId'],
                     'security_schema':operation.get('security',[]),
                     'policy':limiter._buckets(request)})
Path('.unlazy/develop-one/routes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print(f'Inventoried {len(rows)} API operations')
