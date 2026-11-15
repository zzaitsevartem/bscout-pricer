import asyncio

import pytest
from fastapi import Request

from src.config import settings
from src.middleware.client_ip import client_ip
from src.middleware.rate_limit import RateLimitMiddleware
from src.modules.auth.service.auth import create_access_token
from tests.unit.test_rate_limit_redis import FakeRedis

pytestmark = pytest.mark.unit


def request(path="/api/search", method="GET", headers=None, host="192.0.2.1"):
    return Request(
        {
            "type": "http",
            "path": path,
            "method": method,
            "scheme": "http",
            "query_string": b"",
            "server": ("test", 80),
            "headers": [(k.encode(), v.encode()) for k, v in (headers or {}).items()],
            "client": (host, 1234),
        }
    )


def test_proxy_trust_is_scoped_and_resists_spoofing(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_trusted_proxies", "10.0.0.0/24")
    headers = {"x-forwarded-for": "6.6.6.6, 192.0.2.2, 10.0.0.3"}
    assert client_ip(request(headers=headers), True) == "192.0.2.1"
    assert client_ip(request(headers=headers, host="10.0.0.2"), True) == "192.0.2.2"
    assert (
        client_ip(request(headers={"x-forwarded-for": "invalid"}, host="10.0.0.2"), True)
        == "10.0.0.2"
    )


async def test_verified_user_identity_isolated_on_shared_ip():
    redis = FakeRedis()
    limiter = RateLimitMiddleware(None, max_requests=1, redis_factory=lambda: redis)
    a = request(headers={"authorization": f"Bearer {create_access_token(1)}"})
    b = request(headers={"authorization": f"Bearer {create_access_token(2)}"})
    assert await limiter._evaluate(a) is None
    assert (await limiter._evaluate(a)).status_code == 429
    assert await limiter._evaluate(b) is None
    assert limiter._client_key(request(headers={"authorization": "Bearer forged"})) == "192.0.2.1"


async def test_concurrent_workers_share_atomic_budget():
    redis = FakeRedis()
    workers = [
        RateLimitMiddleware(None, max_requests=7, redis_factory=lambda: redis) for _ in range(3)
    ]
    results = await asyncio.gather(*(workers[i % 3]._evaluate(request()) for i in range(50)))
    assert sum(result is None for result in results) == 7
    assert sum(result is not None and result.status_code == 429 for result in results) == 43


@pytest.mark.parametrize(
    ("path", "method", "status"),
    [
        ("/api/search", "GET", None),
        ("/api/auth/login", "POST", 503),
        ("/api/auth/refresh", "POST", None),
        ("/api/auth/logout", "POST", None),
        ("/api/auth/email/resend", "POST", 503),
        ("/api/export/csv", "GET", 503),
        ("/api/admin/import", "POST", 503),
        ("/api/tracking", "POST", 503),
        ("/api/payment/webhook", "POST", 503),
        ("/api/health", "GET", None),
    ],
)
async def test_redis_outage_policy_and_recovery(path, method, status):
    redis = FakeRedis()
    limiter = RateLimitMiddleware(None, redis_factory=lambda: redis)
    redis.fail = True
    response = await limiter._evaluate(request(path, method))
    assert (response.status_code if response else None) == status
    redis.fail = False
    assert await limiter._evaluate(request(path, method)) is None


def test_webhook_separate_from_customer_budget_and_preflight_exempt():
    limiter = RateLimitMiddleware(None)
    assert limiter._buckets(request("/api/payment/webhook", "POST")) == [("webhook", 600, 60)]
    assert limiter._buckets(request(method="OPTIONS")) == []


def test_every_registered_api_route_has_an_explicit_budget():
    from src.main import app

    limiter = RateLimitMiddleware(None)
    paths = app.openapi()["paths"]
    assert paths
    for path, operations in paths.items():
        for method in operations:
            method = method.upper()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
                continue
            buckets = limiter._buckets(request(path, method))
            if path.startswith("/api/health"):
                assert buckets == []
            elif path == "/api/payment/webhook":
                assert buckets == [("webhook", 600, 60)]
            else:
                assert any(scope == "global" for scope, _, _ in buckets), path
                if path.startswith("/api/admin") and method not in {"GET", "HEAD"}:
                    assert any(scope == "expensive" for scope, _, _ in buckets), path


@pytest.mark.parametrize(("peer", "scheme"), [("10.0.0.2", "https"), ("192.0.2.2", "http")])
async def test_redirect_preserves_only_trusted_forwarded_scheme(monkeypatch, peer, scheme):
    import httpx
    from fastapi import FastAPI

    from src.middleware.client_ip import TrustedProxyMiddleware

    monkeypatch.setattr(settings, "rate_limit_trust_forwarded_for", True)
    monkeypatch.setattr(settings, "rate_limit_trusted_proxies", "10.0.0.0/24")
    app = FastAPI()
    app.add_middleware(TrustedProxyMiddleware)

    @app.post("/login")
    async def login():
        return {"ok": True}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app, client=(peer, 1234)),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/login/", headers={"x-forwarded-proto": "https"})
    assert response.status_code == 307
    assert response.headers["location"] == f"{scheme}://testserver/login"


@pytest.mark.parametrize("scheme", ["bearer", "BEARER", "BeArEr"])
async def test_case_insensitive_bearer_cannot_bypass_user_budget(scheme):
    redis = FakeRedis()
    limiter = RateLimitMiddleware(None, max_requests=1, redis_factory=lambda: redis)
    token = create_access_token(123)
    assert await limiter._evaluate(request(headers={"authorization": f"Bearer {token}"})) is None
    response = await limiter._evaluate(request(headers={"authorization": f"{scheme} {token}"}))
    assert response.status_code == 429
