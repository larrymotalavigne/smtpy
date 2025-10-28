"""Security and session middlewares for SMTPy API."""
from __future__ import annotations

import time
from typing import Callable, Awaitable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Sets common security headers on all responses."""

    def __init__(self, app, *, enable_hsts: bool = False) -> None:
        super().__init__(app)
        self.enable_hsts = enable_hsts

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        # Basic security headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-XSS-Protection", "0")
        # Minimal CSP to prevent inline execution; may be relaxed where needed
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; frame-ancestors 'none'; object-src 'none'",
        )
        if self.enable_hsts and request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
        return response


class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    """Enforces idle and absolute session timeouts using signed cookie sessions.

    It relies on a session dict attached to request.state.session or request.session
    provided by Starlette's SessionMiddleware. If not present, it no-ops.
    
    Stored keys in session:
      - _last_access: float epoch seconds of last activity
      - _created_at: float epoch seconds when session created
    """

    def __init__(self, app, *, idle_timeout_seconds: int = 1800, absolute_timeout_seconds: int = 86400) -> None:
        super().__init__(app)
        self.idle_timeout = idle_timeout_seconds
        self.absolute_timeout = absolute_timeout_seconds

    def _get_session(self, request: Request) -> Optional[dict]:
        # Avoid touching request.session property unless SessionMiddleware set the scope
        if isinstance(getattr(request, "scope", None), dict) and "session" in request.scope:
            sess = request.scope.get("session")
            if isinstance(sess, dict):
                return sess
        # Or custom attachment placed by other layers
        return getattr(request.state, "session", None)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        session = self._get_session(request)
        now = time.time()
        if isinstance(session, dict):
            created = float(session.get("_created_at", now))
            last_access = float(session.get("_last_access", now))
            # Absolute timeout check
            if self.absolute_timeout and now - created > self.absolute_timeout:
                session.clear()
                return JSONResponse({"detail": "Session expired (absolute timeout)"}, status_code=440)
            # Idle timeout check
            if self.idle_timeout and now - last_access > self.idle_timeout:
                session.clear()
                return JSONResponse({"detail": "Session expired (idle timeout)"}, status_code=440)
            # Update last access timestamp
            session["_last_access"] = now
            session.setdefault("_created_at", created)
        return await call_next(request)


class SimpleRateLimiter(BaseHTTPMiddleware):
    """Very small in-memory rate limiter for low-traffic/dev usage.

    Limits requests per key (IP or custom key) within a sliding window.
    Not suitable for multi-process or production use without shared storage.
    """

    def __init__(self, app, *, requests: int, window_seconds: int, key_func: Optional[Callable[[Request], str]] = None,
                 paths: Optional[list[str]] = None) -> None:
        super().__init__(app)
        self.max_requests = requests
        self.window = window_seconds
        self.key_func = key_func or (lambda r: r.client.host if r.client else "unknown")
        self.paths = set(paths or [])
        self._hits: dict[str, list[float]] = {}

    def _is_scoped(self, path: str) -> bool:
        if not self.paths:
            return True
        # Simple exact match; could be enhanced to prefix match
        return path in self.paths

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if self._is_scoped(request.url.path):
            key = self.key_func(request)
            now = time.time()
            hits = self._hits.setdefault(key, [])
            # drop old hits outside window
            cutoff = now - self.window
            i = 0
            for ts in hits:
                if ts >= cutoff:
                    break
                i += 1
            if i:
                del hits[:i]
            if len(hits) >= self.max_requests:
                retry_after = int(hits[0] + self.window - now)
                return JSONResponse(
                    {"detail": "Too many requests"},
                    status_code=429,
                    headers={"Retry-After": str(max(retry_after, 1))},
                )
            hits.append(now)
        return await call_next(request)
