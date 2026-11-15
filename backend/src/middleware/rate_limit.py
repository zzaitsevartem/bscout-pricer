import asyncio
import hashlib
import logging
import time
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.security.utils import get_authorization_scheme_param
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.config import settings
from src.middleware.client_ip import client_ip
from src.modules.auth.service.auth import decode_token
from src.modules.cache.service.redis_cache import get_redis

logger = logging.getLogger(__name__)

DEFAULT_NAMESPACE = "ratelimit"
DEFAULT_AUTH_MAX_REQUESTS = 10
DEFAULT_AUTH_WINDOW = 300
DEFAULT_AUTH_PATHS = (
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/password-reset/request",
    "/api/auth/password-reset/confirm",
    "/api/auth/password/change",
)
REDIS_ERRORS = (RedisError, OSError, TimeoutError)
THROTTLED_DETAIL = "Too many requests. Try again later."


class _ResettableCounters(dict):
    def __init__(self, owner: "RateLimitMiddleware") -> None:
        super().__init__()
        self._owner = owner

    def clear(self) -> None:
        super().clear()
        self._owner.rotate_namespace()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        max_requests: int = 60,
        window: int = 60,
        trust_forwarded_for: bool = False,
        auth_max_requests: int | None = None,
        auth_window: int | None = None,
        auth_paths: tuple[str, ...] | None = None,
        namespace: str = DEFAULT_NAMESPACE,
        redis_factory=None,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.trust_forwarded_for = trust_forwarded_for
        self.auth_max_requests = int(
            auth_max_requests
            if auth_max_requests is not None
            else getattr(settings, "auth_rate_limit_max_requests", DEFAULT_AUTH_MAX_REQUESTS)
        )
        self.auth_window = int(
            auth_window
            if auth_window is not None
            else getattr(settings, "auth_rate_limit_window", DEFAULT_AUTH_WINDOW)
        )
        self.auth_paths = tuple(
            auth_paths if auth_paths is not None else DEFAULT_AUTH_PATHS,
        )
        self.namespace = namespace
        self.redis_factory = redis_factory if redis_factory is not None else get_redis
        self._requests = _ResettableCounters(self)
        self._since_sweep = 0

    def rotate_namespace(self) -> str:
        self.namespace = f"{DEFAULT_NAMESPACE}:{uuid4().hex}"
        return self.namespace

    def _client_key(self, request: Request) -> str:
        scheme, token = get_authorization_scheme_param(
            getattr(request, "headers", {}).get("authorization", "")
        )
        if scheme.lower() == "bearer":
            payload = decode_token(token)
            if (
                payload
                and payload.get("type") == "access"
                and str(payload.get("sub", "")).isdigit()
            ):
                return f"user:{payload['sub']}"
        return client_ip(request, self.trust_forwarded_for)

    def _is_auth_path(self, request: Request) -> bool:
        path = getattr(getattr(request, "url", None), "path", "") or ""
        normalized = path.rstrip("/") or "/"
        return any(normalized == candidate.rstrip("/") for candidate in self.auth_paths)

    def _buckets(self, request: Request) -> list[tuple[str, int, int]]:
        path = getattr(getattr(request, "url", None), "path", "").rstrip("/")
        method = getattr(request, "method", "GET")
        if method == "OPTIONS" or path in {"/api/health", "/api/health/live", "/api/health/ready"}:
            return []
        if path == "/api/payment/webhook":
            return [("webhook", 600, 60)]
        buckets = [("global", self.max_requests, self.window)]
        if self._is_auth_path(request) or (
            path.startswith("/api/auth/")
            and path
            not in {"/api/auth/logout", "/api/auth/refresh", "/api/auth/username-available"}
        ):
            buckets.insert(0, ("auth", self.auth_max_requests, self.auth_window))
        if path.startswith(("/api/export", "/api/parser")) or (
            path.startswith("/api/admin") and method not in {"GET", "HEAD"}
        ):
            buckets.insert(0, ("expensive", 10, 60))
        elif path.startswith(("/api/search", "/api/products", "/api/devices")):
            buckets.insert(0, ("search", 90, 60))
        elif method not in {"GET", "HEAD"} and not path.startswith("/api/auth/"):
            buckets.insert(0, ("write", 30, 60))
        return buckets

    async def _consume(self, redis, key: str, limit: int, window: int, now: float) -> bool:
        result = await redis.eval(
            """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local window = tonumber(ARGV[2])
            local limit = tonumber(ARGV[3])
            redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
            if redis.call('ZCARD', key) >= limit then return 0 end
            redis.call('ZADD', key, now, ARGV[4])
            redis.call('EXPIRE', key, window + 1)
            return 1
            """,
            1,
            key,
            now,
            window,
            limit,
            uuid4().hex,
        )
        return bool(result)

    async def _retry_after(self, redis, key: str, window: int, now: float) -> int:
        oldest = await redis.zrange(key, 0, 0, withscores=True)
        if not oldest:
            return max(1, int(window))
        return max(1, int(float(oldest[0][1]) + window - now) + 1)

    def _throttled(self, limit: int, retry_after: int) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": THROTTLED_DETAIL},
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(max(0, limit)),
                "X-RateLimit-Remaining": "0",
            },
        )

    async def _evaluate(self, request: Request) -> JSONResponse | None:
        buckets = self._buckets(request)
        for _, limit, window in buckets:
            if limit <= 0:
                return self._throttled(limit, max(1, int(window)))

        if not buckets:
            return None
        client_key = self._client_key(request)
        now = time.time()
        try:
            redis = self.redis_factory()
            async with asyncio.timeout(1):
                for scope, limit, window in buckets:
                    identity = (
                        client_ip(request, self.trust_forwarded_for)
                        if scope == "auth"
                        else client_key
                    )
                    identity = hashlib.sha256(identity.encode()).hexdigest()
                    key = f"{self.namespace}:{scope}:{identity}"
                    if not await self._consume(redis, key, limit, window, now):
                        return self._throttled(
                            limit, await self._retry_after(redis, key, window, now)
                        )
        except REDIS_ERRORS:
            logger.warning("rate limit store unavailable")
            strict = any(
                scope in {"auth", "expensive", "write", "webhook"} for scope, _, _ in buckets
            )
            if strict:
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "Request protection temporarily unavailable. Try again later."
                    },
                    headers={"Retry-After": "5"},
                )
        return None

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        throttled = await self._evaluate(request)
        if throttled is not None:
            return throttled
        return await call_next(request)
