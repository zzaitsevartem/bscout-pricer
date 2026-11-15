import asyncio
import json
import subprocess
import sys
from uuid import uuid4

import pytest
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from starlette.requests import Request

from src.middleware.rate_limit import RateLimitMiddleware

pytestmark = pytest.mark.integration

WORKER = r"""
import asyncio, sys
import pydantic_settings.sources
pydantic_settings.sources.DotEnvSettingsSource._read_env_files = lambda self: {}
from redis.asyncio import Redis
from starlette.requests import Request
from src.middleware.rate_limit import RateLimitMiddleware
async def main():
    redis = Redis.from_url(sys.argv[1], decode_responses=True)
    limiter = RateLimitMiddleware(
        None, max_requests=12, namespace=sys.argv[2], redis_factory=lambda: redis
    )
    request = Request({'type': 'http', 'path': '/ping', 'method': 'GET', 'scheme': 'http',
                       'headers': [], 'query_string': b'', 'client': ('192.0.2.1', 1234)})
    results = await asyncio.gather(*(limiter._evaluate(request) for _ in range(40)))
    assert all(r is None or r.status_code == 429 for r in results)
    print(sum(r is None for r in results))
    await redis.aclose()
asyncio.run(main())
"""


@pytest.fixture(autouse=True)
def flush_test_redis():
    yield


@pytest.fixture
def redis_url():
    result = subprocess.run(
        ["docker", "run", "--rm", "-d", "-p", "127.0.0.1::6379", "redis:7-alpine"],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    container = result.stdout.strip()
    assert len(container) == 64 and all(c in "0123456789abcdef" for c in container)
    try:
        port = (
            subprocess.check_output(
                ["docker", "port", container, "6379/tcp"],
                text=True,
                timeout=10,
            )
            .strip()
            .rsplit(":", 1)[1]
        )
        yield f"redis://127.0.0.1:{int(port)}/0"
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container], check=True, timeout=15, capture_output=True
        )


async def test_real_redis_shares_atomic_limit_across_processes_and_recovers(redis_url):
    redis = Redis.from_url(redis_url, decode_responses=True)
    try:
        for attempt in range(30):
            try:
                await redis.ping()
                break
            except (OSError, RedisConnectionError):
                if attempt == 29:
                    raise
                await asyncio.sleep(0.1)
        namespace = f"test:{uuid4().hex}"
        processes = [
            await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                WORKER,
                redis_url,
                namespace,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            for _ in range(4)
        ]
        results = await asyncio.wait_for(
            asyncio.gather(*(process.communicate() for process in processes)),
            timeout=60,
        )
        for process, (_, stderr) in zip(processes, results):
            assert process.returncode == 0, stderr.decode()
        assert sum(json.loads(stdout) for stdout, _ in results) == 12
        limiter = RateLimitMiddleware(
            None,
            max_requests=1,
            window=1,
            namespace=f"test:{uuid4().hex}",
            redis_factory=lambda: redis,
        )
        request = Request(
            {
                "type": "http",
                "path": "/ping",
                "method": "GET",
                "scheme": "http",
                "headers": [],
                "query_string": b"",
                "client": ("192.0.2.1", 1234),
            }
        )
        assert await limiter._evaluate(request) is None
        assert (await limiter._evaluate(request)).status_code == 429
        await asyncio.sleep(1.1)
        assert await limiter._evaluate(request) is None
    finally:
        await redis.aclose()
