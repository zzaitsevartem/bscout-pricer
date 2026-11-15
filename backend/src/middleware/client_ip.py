from ipaddress import ip_address, ip_network

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings


def trusted_address(host: str) -> bool:
    try:
        address = ip_address(host)
        return any(
            address in ip_network(item.strip())
            for item in settings.rate_limit_trusted_proxies.split(",")
            if item.strip()
        )
    except ValueError:
        return False


def client_ip(request: Request, trust_forwarded_for: bool | None = None) -> str:
    peer = request.client.host if request.client else "unknown"
    enabled = (
        settings.rate_limit_trust_forwarded_for
        if trust_forwarded_for is None
        else trust_forwarded_for
    )
    if not enabled or not trusted_address(peer):
        return peer
    chain = request.headers.get("x-forwarded-for", "").split(",")
    for host in reversed(chain):
        host = host.strip()
        try:
            ip_address(host)
        except ValueError:
            return peer
        if not trusted_address(host):
            return host
    return peer


class TrustedProxyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        peer = request.client.host if request.client else "unknown"
        if settings.rate_limit_trust_forwarded_for and trusted_address(peer):
            scheme = request.headers.get("x-forwarded-proto", "").lower()
            if scheme in {"http", "https"}:
                request.scope["scheme"] = scheme
        return await call_next(request)
